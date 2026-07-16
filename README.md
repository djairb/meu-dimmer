# Dimmer

Aplicativo de **dimmer de tela** para Windows. Escurece toda a tela por software usando a
Magnification API do Windows (`Magnification.dll`), sem alterar o brilho do monitor. Fica na
bandeja do sistema (system tray) com um pequeno painel de controle.

## Recursos

- Escurece a tela inteira em qualquer nivel (0% a 100%)
- **Scroll** sobre o painel ajusta o dim em passos de 2%
- Icone na bandeja com atalhos rapidos (0 / 25 / 50 / 75 / 100%)
- Clique no icone da bandeja mostra/esconde o painel
- Comeca em 50% de opacidade

## Requisitos

- **Windows** (usa APIs nativas: `user32`, `kernel32`, `Magnification.dll`)
- **Python 3.10+** (desenvolvido com Python 3.14)

## Como rodar em outra maquina

1. Clone o repositorio e entre na pasta:

   ```bash
   git clone <url-do-repo>
   cd "meu dimmer"
   ```

2. Crie e ative um ambiente virtual:

   ```bash
   python -m venv .venv
   # PowerShell
   .venv\Scripts\Activate.ps1
   # ou Git Bash
   source .venv/Scripts/activate
   ```

3. Instale as dependencias:

   ```bash
   pip install PyQt6==6.11.0
   ```

4. Rode o app:

   ```bash
   python dimmer.py
   ```

## Como gerar o executavel (.exe)

O projeto ja inclui o arquivo `dimmer.spec` com a configuracao de build
(single-file, sem janela de console).

1. Com o ambiente virtual ativado, instale o PyInstaller:

   ```bash
   pip install pyinstaller==6.20.0
   ```

2. Gere o executavel:

   ```bash
   pyinstaller dimmer.spec --noconfirm
   ```

3. O executavel final estara em:

   ```
   dist/dimmer.exe
   ```

Basta rodar o `dist/dimmer.exe` diretamente — nao precisa de Python instalado
na maquina onde ele vai ser executado.

## Observacoes

- As pastas `build/`, `dist/` e `.venv/` sao geradas automaticamente e estao no `.gitignore`.
- O arquivo `dimmer.spec` **deve** ser versionado, pois e necessario para reconstruir o `.exe`.
