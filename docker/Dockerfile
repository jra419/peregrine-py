FROM ubuntu:focal

# https://stackoverflow.com/questions/51023312/docker-having-issues-installing-apt-utils
ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Lisbon

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# The install scripts require sudo (no need to clean apt cache, the setup script will install stuff)
RUN apt update
RUN apt install -y sudo

# Create a user with passwordless sudo
RUN adduser --disabled-password --gecos '' docker
RUN adduser docker sudo
RUN echo '%docker ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

USER docker
WORKDIR /home/docker

# Create the shared folder
RUN sudo mkdir /shared
RUN sudo chown -R docker:docker /shared

# Configure ssh directory
RUN mkdir /home/docker/.ssh
RUN chown -R docker:docker /home/docker/.ssh

# Install some nice to have applications
RUN sudo apt -y install \
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
    python3 \
    python3-pip \
    python3.8-venv \
    bash \
    bear \
    clang \
    clang-tools \
    clangd \
    ripgrep \
    shellcheck \
    golang

RUN git clone --branch 0.23.1 https://github.com/junegunn/fzf.git && \
    cd fzf && \
    awk 'NR==110 {$0="	cp -f target/$(BINARY) /usr/bin/fzf"} 1' Makefile > Makefile.tmp && \
    rm Makefile && \
    mv Makefile.tmp Makefile && \
    make && \
    sudo make install && \
    cd .. && \
    rm -r fzf

RUN sudo dpkg-reconfigure --frontend noninteractive tzdata

# Use the provided configs
COPY --chown=docker:docker ./resources/.tmux.conf /home/docker/.tmux.conf
COPY --chown=docker:docker ./resources/.vimrc /home/docker/.vimrc
COPY --chown=docker:docker ./resources/.bashrc /home/docker/.bashrc
COPY --chown=docker:docker ./resources/.inputrc /home/docker/.inputrc
COPY --chown=docker:docker ./resources/alacritty.terminfo /home/docker/alacritty.terminfo

RUN tic -x /home/docker/alacritty.terminfo

RUN echo "source ~/.profile" >> /home/docker/.bash_profile

RUN pip3 install scapy
RUN pip3 install python-lsp-server
RUN pip3 install pandas
RUN pip3 install scipy
RUN pip3 install matplotlib
RUN pip3 install scikit-learn
RUN pip3 install virtualenv
# Fix for https://github.com/protocolbuffers/protobuf/issues/10075
RUN pip3 install -Iv grpcio-tools==1.48.1

# ENIDrift

ENV CONDA_DIR /opt/conda
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh && \
    sudo /bin/bash ~/miniconda.sh -b -p /opt/conda
ENV PATH=$CONDA_DIR/bin:$PATH

RUN conda init bash && \
    . /home/docker/.bashrc && \
    conda create -n env_enidrift python=3.8 && \
    conda activate env_enidrift && \
    conda install pandas -n env_enidrift && \
    conda install -c cctbx202008 scikit-learn -n env_enidrift && \
    conda config --set auto_activate_base false

CMD [ "/bin/bash", "-l"]
