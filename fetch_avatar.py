import os
import hashlib
import requests
import subprocess
import time


GITHUB_TOKEN = "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"


github_auth_header = {"Authorization": f"Bearer {GITHUB_TOKEN}"}

size = 400
output_dir = ".git/avatar"

if not os.path.isdir(".git"):
    print("no .git/ directory found in the current path")
    exit(1)

if not os.path.isdir(output_dir):
    os.mkdir(output_dir)

git_log_command = "git log --pretty=format:\"%ae|%an\""
git_log_process = subprocess.Popen(git_log_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

processed_authors = set()

failed_list = []

for line in git_log_process.stdout:
    line = line.decode("utf-8").strip()
    email, author = line.split("|")

    if author in processed_authors:
        continue

    # Skip authors that are failing
    if line in failed_list:
        continue


    author_image_file = os.path.join(output_dir, author + '.png')

    # Skip images we already have
    if os.path.exists(author_image_file):
        continue

    # Try to fetch the image
    grav_url = f"http://www.gravatar.com/avatar/{hashlib.md5(email.lower().encode()).hexdigest()}?d=404&size={size}"

    print(f"Fetching image for '{author}' {email} ({grav_url})...")
    response = requests.get(grav_url)

    failed = False

    if response.status_code == 200:
        with open(author_image_file, 'wb') as img_file:
            img_file.write(response.content)
        time.sleep(1)
    else:
        failed = True

    if failed:
        print("trying Github email")

        github_api = f"https://api.github.com/search/users?q={email}"

        response = requests.get(github_api, headers=github_auth_header)
        if response.status_code == 200:
            response_json = response.json()
            if response_json["total_count"] > 0:
                github_url = response_json["items"][0]["avatar_url"]
                print(f"Fetching image for '{author}' {email} ({github_url})...")
                response = requests.get(github_url+"?size="+str(size), headers=github_auth_header)
                if response.status_code == 200:
                    with open(author_image_file, 'wb') as img_file:
                        img_file.write(response.content)
                    time.sleep(1)
                    failed = False
                elif response.status_code == 403:
                    print("Github rate limit exceeded, try again later")
                    exit(1)
                
    if failed:
        print("trying Github username")
        github_api = f"https://api.github.com/users/{author}"

        response = requests.get(github_api, headers=github_auth_header)
        if response.status_code == 200:
            response_json = response.json()
            if response_json["avatar_url"] is not None:
                github_url = response_json["avatar_url"]
                print(f"Fetching image for '{author}' {email} ({github_url})...")
                response = requests.get(github_url+"?size="+str(size), headers=github_auth_header)
                if response.status_code == 200:
                    with open(author_image_file, 'wb') as img_file:
                        img_file.write(response.content)
                    time.sleep(1)
                    failed = False
                elif response.status_code == 403:
                    print("Github rate limit exceeded, try again later")
                    exit(1)


        

    if failed:
        print(f"Failed to fetch image for '{author}' {email} ({grav_url})")
        failed_list.append(str(line))

with open("failed.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(failed_list))

git_log_process.stdout.close()
git_log_process.stderr.close()
