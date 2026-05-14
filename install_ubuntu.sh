#!/bin/bash
# Automated Appointment Tester - Ubuntu install script

echo "================================"
echo "Appointment Tester install"
echo "================================"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

WORK_DIR="/opt/appointment-tester"

if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root (sudo)${NC}"
    exit 1
fi

echo -e "${YELLOW}[1/6] Updating system...${NC}"
apt update

echo -e "${YELLOW}[2/6] Checking Python 3.10...${NC}"
if ! command -v python3.10 &> /dev/null; then
    echo "Installing Python 3.10..."
    apt install software-properties-common -y
    add-apt-repository ppa:deadsnakes/ppa -y
    apt update
    apt install python3.10 python3.10-venv python3.10-dev -y
fi

echo -e "${YELLOW}[3/6] Installing Playwright system deps...${NC}"
apt install -y \
    libnss3 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libgbm1 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0 \
    libcups2 \
    libgtk-3-0

echo -e "${YELLOW}[4/6] Creating Python virtualenv...${NC}"
cd $WORK_DIR
python3.10 -m venv venv
source venv/bin/activate

echo -e "${YELLOW}[5/6] Installing Python packages...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

echo -e "${YELLOW}[6/6] Installing Playwright browsers...${NC}"
playwright install chromium
playwright install-deps chromium

if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env from example...${NC}"
    cp .env.example .env
    echo -e "${RED}Remember to edit .env before starting the service.${NC}"
fi

echo -e "${YELLOW}Creating systemd service...${NC}"

cat > /etc/systemd/system/appointment-tester.service << EOF
[Unit]
Description=Automated Appointment Tester
After=network.target

[Service]
Type=simple
User=www
WorkingDirectory=$WORK_DIR
Environment=PATH=$WORK_DIR/venv/bin:/usr/local/bin:/usr/bin
ExecStart=$WORK_DIR/venv/bin/python main.py
Restart=on-failure
RestartSec=30
StandardOutput=append:$WORK_DIR/bot.log
StandardError=append:$WORK_DIR/bot_error.log

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Install complete${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo -e "Next steps:"
echo -e "1. ${YELLOW}Edit the .env file:${NC}"
echo -e "   nano $WORK_DIR/.env"
echo ""
echo -e "2. ${YELLOW}Run a manual smoke test:${NC}"
echo -e "   cd $WORK_DIR && source venv/bin/activate && python main.py"
echo ""
echo -e "3. ${YELLOW}Enable the service:${NC}"
echo -e "   systemctl enable appointment-tester"
echo -e "   systemctl start appointment-tester"
echo ""
echo -e "4. ${YELLOW}Check logs:${NC}"
echo -e "   tail -f $WORK_DIR/bot.log"
echo ""
