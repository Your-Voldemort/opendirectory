import asyncio
import os
import json
import re
import time
import random
import datetime
from typing import Coroutine, Any, Optional
import aiohttp
from dotenv import load_dotenv

load_dotenv()

TARGET_OWNER = os.environ.get("TARGET_OWNER")
if not TARGET_OWNER:
    raise ValueError("TARGET_OWNER environment variable is not set")

TARGET_REPO = os.environ.get("TARGET_REPO")
if not TARGET_REPO:
    raise ValueError("TARGET_REPO environment variable is not set")

MAX_USERS = int(os.environ.get("MAX_USERS", "25000"))
MAX_CONCURRENT = int(os.environ.get("MAX_CONCURRENT", "10"))

API_BASE_URL = "https://api.github.com"
OUTPUT_FILENAME = f"{TARGET_OWNER}_{TARGET_REPO}_detailed.jsonl"


class Token:
    def __init__(self, pat: str):
        self.pat = pat
        self.rate_limit_reset = 0.0
        self.search_lock = asyncio.Lock()
        self.last_search_time = 0.0


class TokenPool:
    def __init__(self, pats: list[str]):
        if not pats:
            raise ValueError("No GITHUB_PATS provided")
        self.tokens = [Token(pat.strip()) for pat in pats if pat.strip()]
        if not self.tokens:
            raise ValueError("No valid GITHUB_PATS provided")
        self.lock = asyncio.Lock()
        self.current_index = 0

    async def get_token(self) -> Token:
        while True:
            async with self.lock:
                now = time.time()
                for _ in range(len(self.tokens)):
                    token = self.tokens[self.current_index]
                    self.current_index = (self.current_index + 1) % len(self.tokens)
                    if token.rate_limit_reset <= now:
                        return token

                soonest_reset = min(t.rate_limit_reset for t in self.tokens)
                sleep_time = max(0.1, soonest_reset - now)

            print(f"All tokens rate limited. Sleeping for {sleep_time:.2f} seconds...")
            await asyncio.sleep(sleep_time)

    async def mark_rate_limited(self, token: Token, reset_time: float):
        async with self.lock:
            token.rate_limit_reset = max(token.rate_limit_reset, reset_time)


# Initialize TokenPool
pats_env = os.environ.get("GITHUB_PATS")
if not pats_env:
    raise ValueError(
        "GITHUB_PATS environment variable is not set in the environment or .env file"
    )

token_pool = TokenPool(pats_env.split(","))


def validate_email(email: Optional[str], username: str) -> bool:
    if not email or not isinstance(email, str):
        return False
    email = email.strip().lower()
    if not email:
        return False
    if "noreply.github.com" in email:
        return False
    if "dependabot" in email or "github-actions" in email:
        return False
    return True


async def send_req_until_success(
    method: str, url: str, is_search: bool = False, **kwargs
) -> Any:
    delay_sec = 2
    retry_number = 0
    while True:
        retry_number += 1
        token = await token_pool.get_token()

        if is_search:
            async with token.search_lock:
                now = time.time()
                elapsed = now - token.last_search_time
                if elapsed < 2.1:
                    await asyncio.sleep(2.1 - elapsed)
                token.last_search_time = time.time()

        headers = kwargs.get("headers", {})
        headers["Authorization"] = f"Bearer {token.pat}"
        headers["Accept"] = "application/vnd.github.v3+json"
        kwargs["headers"] = headers

        await asyncio.sleep(random.uniform(0.1, 0.4))

        try:
            async with aiohttp.request(method, url, **kwargs) as res:
                if res.status == 401:
                    print(
                        f"Unauthorized token: {token.pat[:4]}... Marking as rate limited for 60s."
                    )
                    await token_pool.mark_rate_limited(token, time.time() + 60)
                    continue
                if res.status == 404:
                    return {}
                if res.status == 403 or res.status == 429:
                    retry_after = res.headers.get("Retry-After")
                    if retry_after:
                        reset_time = time.time() + float(retry_after) + 1.0
                    else:
                        reset_header = res.headers.get("x-ratelimit-reset")
                        if reset_header:
                            reset_time = float(reset_header) + 1.0
                        else:
                            reset_time = time.time() + (delay_sec * retry_number)

                    await token_pool.mark_rate_limited(token, reset_time)
                    continue
                if res.status != 200:
                    if res.status < 500:
                        return {}
                    print(f"Server error {res.status} for {url}, retrying...")
                    await asyncio.sleep(delay_sec)
                    continue
                json_resp = await res.json()
                return json_resp
        except Exception as e:
            await asyncio.sleep(delay_sec)
            continue


async def get_stargazers(url: str, page: int) -> list[str]:
    params = {
        "per_page": "100",
        "page": str(page),
    }
    resp = await send_req_until_success("GET", url, params=params)
    if isinstance(resp, list):
        return [u["login"] for u in resp if "login" in u]
    return []


async def get_all_stargazers(owner: str, repo: str) -> list[str]:
    url = f"{API_BASE_URL}/repos/{owner}/{repo}/stargazers"
    res = []
    page = 1
    while True:
        print(f"Fetching stargazers page {page}...")
        stargazers = await get_stargazers(url, page)
        if not stargazers:
            break
        res.extend(stargazers)
        if len(res) >= MAX_USERS:
            res = res[:MAX_USERS]
            break
        page += 1
    return res


async def get_user_profile(username: str) -> dict:
    """Fetch basic profile data via REST API."""
    url = f"{API_BASE_URL}/users/{username}"
    resp = await send_req_until_success("GET", url)
    return resp if isinstance(resp, dict) else {}


async def get_emails_from_events(username: str) -> tuple[set, list]:
    """Fallback 1: Extract emails from Public PushEvents via REST."""
    url = f"{API_BASE_URL}/users/{username}/events/public"
    resp = await send_req_until_success("GET", url)

    extracted_emails = set()
    commit_urls = []
    if isinstance(resp, list):
        for event in resp:
            if event.get("type") == "PushEvent":
                commits = event.get("payload", {}).get("commits", [])
                for commit in commits:
                    author = commit.get("author", {})
                    email = author.get("email")
                    if validate_email(email, username):
                        extracted_emails.add(email)
                    url = commit.get("url")
                    if url:
                        commit_urls.append(url)
    return extracted_emails, commit_urls


async def get_emails_from_gpg(username: str) -> set:
    url = f"{API_BASE_URL}/users/{username}/gpg_keys"
    resp = await send_req_until_success("GET", url)
    extracted_emails = set()
    if isinstance(resp, list):
        for key in resp:
            emails = key.get("emails", [])
            for email_obj in emails:
                email = email_obj.get("email")
                if validate_email(email, username):
                    extracted_emails.add(email)
    return extracted_emails


async def get_emails_from_patch(commit_urls: list[str]) -> set:
    extracted_emails = set()
    for url in commit_urls:
        patch_url = url + ".patch"
        try:
            await asyncio.sleep(random.uniform(0.1, 0.4))
            async with aiohttp.request("GET", patch_url) as res:
                if res.status == 200:
                    text = await res.text()
                    match = re.search(r"^From:\s+.*?\s+<([^>]+)>", text, re.MULTILINE)
                    if match:
                        email = match.group(1)
                        if validate_email(email, ""):
                            extracted_emails.add(email)
        except Exception:
            pass
    return extracted_emails


async def get_emails_from_global_search(username: str) -> set:
    extracted_emails = set()
    url = (
        f"{API_BASE_URL}/search/commits?q=author:{username}&sort=author-date&order=desc"
    )

    try:
        resp = await send_req_until_success("GET", url, is_search=True)
        items = resp.get("items", [])
        for item in items:
            author = item.get("author")
            if author and author.get("login", "").lower() == username.lower():
                commit = item.get("commit", {})
                author_data = commit.get("author", {})
                email = author_data.get("email")
                if validate_email(email, username):
                    extracted_emails.add(email)
    except Exception:
        pass

    return extracted_emails


async def get_emails_from_graphql(username: str) -> set:
    url = "https://api.github.com/graphql"
    query = """
    query GetRecentCommits($login: String!) {
      user(login: $login) {
        repositories(
          first: 20
          isFork: false
          ownerAffiliations: OWNER
          orderBy: {field: PUSHED_AT, direction: DESC}
        ) {
          nodes {
            defaultBranchRef {
              target {
                ... on Commit {
                  history(first: 10) {
                    nodes {
                      author {
                        email
                        user {
                          login
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
    """

    resp = await send_req_until_success(
        "POST", url, json={"query": query, "variables": {"login": username}}
    )

    extracted_emails = set()
    try:
        repos = (
            resp.get("data", {})
            .get("user", {})
            .get("repositories", {})
            .get("nodes", [])
        )
        for repo in repos:
            if not repo or not repo.get("defaultBranchRef"):
                continue
            commits = repo["defaultBranchRef"]["target"]["history"]["nodes"]
            for commit in commits:
                author_data = commit.get("author", {})
                github_user = author_data.get("user")

                if (
                    github_user
                    and github_user.get("login", "").lower() == username.lower()
                ):
                    email = author_data.get("email")
                    if email and "noreply.github.com" not in email:
                        extracted_emails.add(email)
    except Exception as e:
        pass

    return extracted_emails


async def process_user(username: str) -> dict:
    profile = await get_user_profile(username)
    email = profile.get("email")

    if not validate_email(email, username):
        email = None

    if not email:
        events_emails, commit_urls = await get_emails_from_events(username)
        if events_emails:
            email = list(events_emails)[0]

        if not email:
            gpg_emails = await get_emails_from_gpg(username)
            if gpg_emails:
                email = list(gpg_emails)[0]

            if not email:
                if commit_urls:
                    patch_emails = await get_emails_from_patch(commit_urls)
                    if patch_emails:
                        email = list(patch_emails)[0]

                if not email:
                    search_emails = await get_emails_from_global_search(username)
                    if search_emails:
                        email = list(search_emails)[0]

    return {
        "login": username,
        "email": email,
        "name": profile.get("name"),
        "location": profile.get("location"),
        "company": profile.get("company"),
        "blog": profile.get("blog"),
        "twitter": profile.get("twitter_username"),
        "followers": profile.get("followers"),
        "public_repos": profile.get("public_repos"),
        "profile_url": profile.get("html_url"),
        "email_found": bool(email),
    }


def load_processed_users(filename: str) -> set[str]:
    processed = set()
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        data = json.loads(line)
                        if "login" in data:
                            processed.add(data["login"])
                    except json.JSONDecodeError:
                        pass
    return processed


async def main():
    print(f"Targeting: {TARGET_OWNER}/{TARGET_REPO}")

    stargazers_list = await get_all_stargazers(TARGET_OWNER, TARGET_REPO)
    stargazers = []
    seen = set()
    for u in stargazers_list:
        if u not in seen:
            seen.add(u)
            stargazers.append(u)

    print("Stargazers count:", len(stargazers))

    processed_users = load_processed_users(OUTPUT_FILENAME)
    print(f"Already processed: {len(processed_users)}")

    to_process = [u for u in stargazers if u not in processed_users]
    total_to_process = len(to_process)
    print(f"Remaining to process: {total_to_process}")

    if not to_process:
        print("All users processed.")
        return

    file_lock = asyncio.Lock()
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    processed_count = 0
    start_time = time.time()

    PRINT_INTERVAL = 20

    async def process_and_save(username: str):
        nonlocal processed_count
        async with semaphore:
            result = await process_user(username)
            async with file_lock:
                with open(OUTPUT_FILENAME, "a", encoding="utf-8") as f:
                    f.write(json.dumps(result, ensure_ascii=False) + "\n")

                processed_count += 1
                if (
                    processed_count % PRINT_INTERVAL == 0
                    or processed_count == total_to_process
                ):
                    elapsed = time.time() - start_time
                    rate = processed_count / elapsed if elapsed > 0 else 0
                    remaining = total_to_process - processed_count
                    eta_seconds = remaining / rate if rate > 0 else 0
                    eta_str = str(datetime.timedelta(seconds=int(eta_seconds)))
                    print(
                        f"[{processed_count}/{total_to_process}] Rate: {rate:.2f} users/sec | ETA: {eta_str}"
                    )

    tasks = [asyncio.create_task(process_and_save(username)) for username in to_process]
    await asyncio.gather(*tasks)

    print(f"Finished writing deep extraction results to {OUTPUT_FILENAME}")


if __name__ == "__main__":
    asyncio.run(main())
