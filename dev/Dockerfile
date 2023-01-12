FROM ubuntu:focal

# https://stackoverflow.com/questions/51023312/docker-having-issues-installing-apt-utils
ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Lisbon

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# The install scripts require sudo (no need to clean apt cache, the setup script will install stuff)
RUN apt-get update && apt-get install -y sudo

# Create a user with passwordless sudo
RUN adduser --disabled-password --gecos '' docker
RUN adduser docker sudo
RUN echo '%docker ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

USER docker
WORKDIR /home/docker

# Configure ssh directory
RUN mkdir /home/docker/.ssh
RUN chown -R docker:docker /home/docker/.ssh

# Install some nice to have applications
RUN sudo apt-get -y install \
    man \
    build-essential \
    wget \
    curl \
    git \
    vim \
    tzdata \
    tmux \
    iputils-ping \
    iproute2 \
    net-tools \
    tcpreplay \
    iperf \
    psmisc \
    htop \
    gdb \
    xdot \
    xdg-utils \
    libcanberra-gtk-module \
    libcanberra-gtk3-module \
    zsh \
    python3

RUN sudo dpkg-reconfigure --frontend noninteractive tzdata

# Installing terminal sugar
RUN curl -fsSL https://raw.githubusercontent.com/zimfw/install/master/install.zsh | zsh

# Change default shell
RUN sudo chsh -s $(which zsh) 

######################
#  Building SDE env  #
######################

# Copy scripts and files into the workspace
COPY --chown=docker:docker ./scripts/build-p4.sh /opt/scripts/build-p4.sh
COPY --chown=docker:docker ./scripts/build-barefoot-sde.sh /opt/scripts/build-barefoot-sde.sh
COPY --chown=docker:docker ./resources /opt/files

# Make scripts executable
RUN chmod +x /opt/scripts/build-p4.sh
RUN chmod +x /opt/scripts/build-barefoot-sde.sh

COPY --chown=docker:docker ./resources/patches.tgz /opt/files/patches.tgz
COPY --chown=docker:docker ./resources/bf-sde-9.7.0.tgz /opt/files/bf-sde-9.7.0.tgz
COPY --chown=docker:docker ./resources/bf-reference-bsp-9.7.0.tgz /opt/files/bf-reference-bsp-9.7.0.tgz
COPY --chown=docker:docker ./resources/ica-tools.tgz /opt/files/ica-tools.tgz

RUN /opt/scripts/build-p4.sh
RUN /opt/scripts/build-barefoot-sde.sh

CMD [ "/usr/bin/zsh" ]