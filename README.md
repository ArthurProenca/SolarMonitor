
# ☀️ Solaire ☀️

Bem-vindo ao repositório do projeto Solaire! Este README fornece instruções sobre como configurar o ambiente Python 3.8, instalar o pip e instalar todas as dependências necessárias a partir do arquivo `requirements.txt`.

## 🌞 Sumário

1. [Pré-requisitos](#pré-requisitos)
2. [Instalação do Python 3.8](#instalação-do-python-38)
3. [Instalação do pip](#instalação-do-pip)
4. [Instalação das dependências](#instalação-das-dependências)
5. [Execução do projeto](#execução-do-projeto)

## 🌅 Pré-requisitos

Antes de começar, certifique-se de ter acesso a uma conexão com a internet e permissões de administrador no seu sistema.

## 🌟 Instalação do Python 3.8

### Windows

1. Baixe o instalador do Python 3.8 [aqui](https://www.python.org/downloads/release/python-380/).
2. Execute o instalador e siga as instruções na tela.
3. **Importante:** Marque a opção "Add Python to PATH" durante a instalação.

### Linux

1. Abra o Terminal.
2. Atualize os repositórios de pacotes:
   ```bash
   sudo apt update
   ```
3. Instale o Python 3.8:
   ```bash
   sudo apt install python3.8
   ```

## 🌻 Instalação do pip

O pip geralmente é instalado automaticamente com o Python. Para verificar se o pip está instalado corretamente, execute:
   ```bash
   pip --version
   ```

Se o pip não estiver instalado, você pode instalá-lo manualmente:

### Windows

1. Baixe o script `get-pip.py`:
   ```bash
   curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
   ```
2. Execute o script:
   ```bash
   python get-pip.py
   ```

### Linux

1. Use o seguinte comando:
   ```bash
   sudo apt install python3-pip
   ```

## 🌺 Instalação das dependências

Com o Python e o pip instalados, você pode instalar todas as dependências necessárias a partir do arquivo `requirements.txt`.

1. Navegue até o diretório do projeto Solaire:
   ```bash
   cd caminho/para/seu/projeto
   ```
2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

## 🌞 Execução do projeto

Agora que todas as dependências estão instaladas, você pode executar o projeto Solaire.

1. Navegue até o diretório do projeto, se ainda não estiver lá:
   ```bash
   cd caminho/para/seu/projeto
   ```
2. Navegue até a pasta /app:
   ```bash
   cd app
   ```
3. Execute o projeto:
   ```bash
   uvicorn main:app --reload
   ```

Divirta-se explorando o projeto Solaire! ☀️
