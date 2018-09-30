# Arnold

Arnold is a helpful tool for the UCCSER GitHub repositories.
This tool is created for use only within our organisation, however the source code is freely available.
Currently Arnold runs on a Google Cloud Platform Compute instance on a schedule, and when required.

Arnold is still in development, but here are some of his features:

- Check for broken URL links.
- Update Django message files.
- Push, build, and pull translations to and from Crowdin.
- Logging to Google Cloud Platform logging.

The following features are planned for Arnold one day:

- Support of managing in-context translations on Crowdin.
- Test suite.

## Installation

Create Google Cloud Platform Compute instance (1v CPU, 6.5GB memory, 25GB Ubuntu 16.04 LTS disk).
Connect via SSH and perform the followings installation steps:

```bash
# Set default user password
sudo passwd ${USER}

# Install Git, Python3 pip, Docker, and Docker Compose
sudo apt-get install -y \
    git \
    python3-pip \
    apt-transport-https \
    ca-certificates \
    curl \
    software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
sudo apt-get update
apt-cache policy docker-ce
sudo apt-get install -y docker-ce
sudo usermod -aG docker ${USER}
su - ${USER}
id -nG
sudo curl -L https://github.com/docker/compose/releases/download/1.22.0/docker-compose-`uname -s`-`uname -m` -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Setup GitHub SSH
ssh-keygen -t rsa -b 4096 -C "${BOT_EMAIL}"
eval $(ssh-agent -s)
ssh-add ~/.ssh/id_rsa

# Clone repo
git clone git@github.com:uccser/arnold.git
# Answer Yes to trust GitHub

# Upload secrets YAML file
mv secrets.yaml arnold/secrets.yaml
cd arnold/
pip3 install -r requirements.txt
```

## Usage

First connect via SSH and change into the Arnold directory (`cd arnold`).
To run Arnold with default settings, enter the following command: `python3 run.py [TASK]`, where task is one of the following:

- `link-checker`: Check for broken links
- `update-source-message-files`: Update source message files
- `push-source-files`: Push source files to Crowdin
- `build-project`: Build project on Crowdin
- `pull-translations`: Pull translations from Crowdin
- `all`: Run all tasks

The following flags can also be used:

- `--repo REPO` or `-r REPO`: Run only on the given repository, where `REPO` is the project slug (for example: `cs-unplugged`)
- `--skip-clone` or `-c`: Skip cloning repositories (not recommended)

## Schedule

The server has the following tasks set via `cron` tasks.

| Task                          | UTC Time | NZST Time | NZDT Time |
|-------------------------------|----------|-----------|-----------|
| `update-source-message-files` | 3 AM     | 3 PM      | 4 PM      |
| `push-source-files`           | 10 AM    | 10 PM     | 11 PM     |
| `build-project`               | 2 PM     | 2 AM      | 3 AM      |
| `pull-translations`           | 7 PM     | 7 AM      | 8 AM      |
| `link-checker`                | 11 PM    | 11 AM     | 12 PM     |

The raw crontab is as follows:

```
0 3 * * * cd /home/csse_education_research/arnold/ && python3 run.py update-source-message-files
0 10 * * * cd /home/csse_education_research/arnold/ && python3 run.py push-source-files
0 14 * * * cd /home/csse_education_research/arnold/ && python3 run.py build-project
0 19 * * * cd /home/csse_education_research/arnold/ && python3 run.py pull-translations
0 23 * * * cd /home/csse_education_research/arnold/ && python3 run.py link-checker
```
