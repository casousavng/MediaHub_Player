#!/bin/bash

# Setup Script para o Media Hub
# Verifica e instala dependências no macOS

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
NC='\033[0m' # Sem Cor

echo -e "${CYAN}====================================================${NC}"
echo -e "${CYAN}       🔧 Media Hub (Rádio & YouTube) - Setup       ${NC}"
echo -e "${CYAN}====================================================${NC}"
echo ""

# 1. Verificar se o sistema operativo é macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${RED}Erro: Este script de configuração foi desenhado apenas para macOS.${NC}"
    exit 1
fi

# 2. Verificar se o Homebrew está instalado
if ! command -v brew &> /dev/null; then
    echo -e "${YELLOW}Aviso: O Homebrew não foi detetado no teu sistema.${NC}"
    echo -e "O Homebrew é necessário para instalar as dependências de sistema."
    echo -e "Queres instalar o Homebrew agora? (s/n)"
    read -r install_brew
    if [[ "$install_brew" =~ ^[Ss]$ ]]; then
        echo "A instalar o Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    else
        echo -e "${RED}Erro: O Homebrew é necessário para continuar. Abortado.${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✓ Homebrew detetado.${NC}"

# 3. Verificar/Instalar mpv
if ! command -v mpv &> /dev/null; then
    echo -e "${YELLOW}mpv não encontrado. A instalar via Homebrew...${NC}"
    brew install mpv
else
    echo -e "${GREEN}✓ mpv já está instalado.${NC}"
fi

# 4. Verificar/Instalar yt-dlp
if ! command -v yt-dlp &> /dev/null; then
    echo -e "${YELLOW}yt-dlp não encontrado. A instalar via Homebrew...${NC}"
    brew install yt-dlp
else
    echo -e "${GREEN}✓ yt-dlp já está instalado.${NC}"
fi

# 5. Verificar/Instalar SwiftBar
if [ ! -d "/Applications/SwiftBar.app" ] && [ ! -d "$HOME/Applications/SwiftBar.app" ]; then
    echo -e "${YELLOW}SwiftBar.app não foi encontrado na pasta Aplicações.${NC}"
    echo -e "Queres instalar o SwiftBar via Homebrew Cask? (s/n)"
    read -r install_sb
    if [[ "$install_sb" =~ ^[Ss]$ ]]; then
        brew install --cask swiftbar
    else
        echo -e "${YELLOW}Aviso: Lembra-te de instalar o SwiftBar manualmente para a interface gráfica.${NC}"
    fi
else
    echo -e "${GREEN}✓ SwiftBar já está instalado nas Aplicações.${NC}"
fi

# 6. Tornar o script executável
SCRIPT_FILE="media_player.5s.py"
if [ -f "$SCRIPT_FILE" ]; then
    chmod +x "$SCRIPT_FILE"
    echo -e "${GREEN}✓ Permissões de execução atribuídas a $SCRIPT_FILE.${NC}"
else
    echo -e "${RED}Erro: Não foi possível encontrar o ficheiro $SCRIPT_FILE no diretório atual.${NC}"
fi

echo ""
echo -e "${CYAN}====================================================${NC}"
echo -e "${GREEN}🎉 Configuração concluída com sucesso!${NC}"
echo -e "${CYAN}====================================================${NC}"
echo ""
echo -e "Para correr o Media Hub:"
echo -e "1. Garante que copiaste o ficheiro ${YELLOW}media_player.5s.py${NC} para a pasta de plugins do teu SwiftBar."
echo -e "2. Podes abrir o painel TUI interativo executando: ${YELLOW}python3 media_player.5s.py${NC} no Terminal."
echo ""
