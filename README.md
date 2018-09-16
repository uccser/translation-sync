# Arnold

Arnold is a helpful tool for the UCCSER GitHub repositories.
This tool is created for use only within our organisation, however the source code is freely available.
Currently Arnold runs on a Google Cloud Platform Compute instance on a schedule, and when required.

Arnold is still in development, but here are some of his features:

- Check for broken URL links.
- Update Django message files.
- Push, build, and pull translations to and from Crowdin.

The following features are planned for Arnold one day:

- Support of managing in-context translations on Crowdin.
- Test suite.
- Error logging, possibly also by email and Slack.

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
To run Arnold with default settings, enter the following command: `python3 run.py`

The following flags can also be used:

- `--repo REPO` or `-r REPO`: Run only on the given repository, where `REPO` is the project slug (for example: `cs-unplugged`)
- `--skip-link-checker` or `-lc`: Skip checking for broken links
- `--skip-clone` or `-c`: Skip cloning repositories
