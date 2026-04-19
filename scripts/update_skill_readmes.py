import os

markdown_snippet = """## Installation in Claude Desktop App

### Video Tutorial
Watch this quick video to see how it's done:

https://github.com/user-attachments/assets/ee98a1b5-ebc4-452f-bbfb-c434f2935067

### Step 1: Download the skill from GitHub
1. Copy the URL of this specific skill folder from your browser's address bar.
2. Go to [download-directory.github.io](https://download-directory.github.io/).
3. Paste the URL and click **Enter** to download.

### Step 2: Install the Skill in Claude
1. Open your **Claude desktop app**.
2. Go to the sidebar on the left side and click on the **Customize** section.
3. Click on the **Skills** tab, then click on the **+** (plus) icon button to create a new skill.
4. Choose the option to **Upload a skill**, and drag and drop the `.zip` file (or you can extract it and drop the folder, both work).

> **Note:** For some skills (like `position-me`), the `SKILL.md` file might be located inside a subfolder. Always make sure you are uploading the specific folder that contains the `SKILL.md` file!
"""

def update_readmes(base_dir="skills"):
    if not os.path.exists(base_dir):
        print(f"Error: {base_dir} directory not found.")
        return

    for root, dirs, files in os.walk(base_dir):
        if root == base_dir:
            for skill_dir in dirs:
                readme_path = os.path.join(root, skill_dir, "README.md")
                
                if os.path.exists(readme_path):
                    with open(readme_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    if "## Installation in Claude Desktop App" in content:
                        content = content.split("## Installation in Claude Desktop App")[0].strip()
                    elif "## Installation in Claude" in content:
                        content = content.split("## Installation in Claude")[0].strip()
                    
                    with open(readme_path, "w", encoding="utf-8") as f:
                        f.write(content + "\n\n" + markdown_snippet)
                    
                    print(f"Updated: {readme_path}")
                else:
                    print(f"No README.md found in: {os.path.join(root, skill_dir)}, creating one...")
                    with open(readme_path, "w", encoding="utf-8") as f:
                        f.write(f"# {skill_dir}\n\n")
                        f.write(markdown_snippet)
                    print(f"Created and Updated: {readme_path}")
            break

if __name__ == "__main__":
    # Ensure it runs correctly even if called from scripts directory
    if os.path.basename(os.getcwd()) == "scripts":
        os.chdir("..")
    update_readmes("skills")
