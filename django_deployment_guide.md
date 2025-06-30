# Guide de déploiement Django avec PostgreSQL et Nginx

## 1. Mise à jour du système

```bash
apt update && apt upgrade -y
```

## 2. Installation des dépendances système

```bash
# Installation des paquets essentiels
apt install -y python3 python3-pip python3-venv git nginx postgresql postgresql-contrib certbot python3-certbot-nginx

# Installation de dépendances pour PostgreSQL et Python
apt install -y libpq-dev python3-dev build-essential
```

## 3. Configuration de PostgreSQL

```bash
# Démarrer et activer PostgreSQL
systemctl start postgresql
systemctl enable postgresql

# Se connecter à PostgreSQL en tant que postgres
sudo -u postgres psql
```

Dans PostgreSQL, créez la base de données et l'utilisateur :

```sql
-- Créer la base de données
CREATE DATABASE cookfamily_db;

-- Créer l'utilisateur
CREATE USER cookfamily_user WITH PASSWORD 'votre_mot_de_passe_securise';

-- Accorder les privilèges
ALTER ROLE cookfamily_user SET client_encoding TO 'utf8';
ALTER ROLE cookfamily_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE cookfamily_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE cookfamily_db TO cookfamily_user;

-- Quitter PostgreSQL
\q
```

## 4. Déploiement de l'application Django

```bash
# Créer le répertoire pour l'application
mkdir -p /var/www
cd /var/www

# Cloner votre repository
git clone https://github.com/votre-username/cook.git
cd cook

# Créer l'environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances Python
pip install -r requirements.txt

# Si pas de requirements.txt, installer les essentiels
pip install django gunicorn psycopg2-binary python-decouple
```

## 5. Configuration Django

Créez un fichier `.env` dans le répertoire de votre projet :



## 6. Migration et collecte des fichiers statiques

```bash
# Activer l'environnement virtuel
source /var/www/cook/venv/bin/activate

# Migrations Django
python manage.py makemigrations
python manage.py migrate

# Collecter les fichiers statiques
python manage.py collectstatic --noinput

# Créer un superutilisateur (optionnel)
python manage.py createsuperuser
```

## 7. Configuration de Gunicorn

Créez un fichier de service systemd pour Gunicorn :

```bash
# /etc/systemd/system/gunicorn-cook.service
[Unit]
Description=gunicorn daemon for Cook Django project
After=network.target

[Service]
User=root
Group=www-data
WorkingDirectory=/var/www/cook
ExecStart=/var/www/cook/venv/bin/gunicorn --access-logfile - --workers 3 --bind 127.0.0.1:8000 cook.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

Activez et démarrez le service :

```bash
systemctl daemon-reload
systemctl start gunicorn-cook
systemctl enable gunicorn-cook
systemctl status gunicorn-cook
```

## 8. Configuration Nginx (version propre)

Créez le fichier de configuration Nginx :

```bash
# /etc/nginx/sites-available/cookfamily
# Redirige tout le trafic HTTP vers HTTPS
server {
    listen 80;
    server_name cookfamily.fr www.cookfamily.fr;
    return 301 https://$host$request_uri;
}

# Configuration HTTPS avec Let's Encrypt
server {
    listen 443 ssl http2;
    server_name cookfamily.fr www.cookfamily.fr;
    
    # Limite de taille des uploads
    client_max_body_size 50M;
    
    # Certificats SSL (seront générés par Certbot)
    ssl_certificate /etc/letsencrypt/live/cookfamily.fr/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/cookfamily.fr/privkey.pem;
    
    # Configuration SSL moderne
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA384;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Headers de sécurité
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Logging
    access_log /var/log/nginx/cookfamily_access.log;
    error_log /var/log/nginx/cookfamily_error.log;
    
    # Favicon
    location = /favicon.ico {
        access_log off;
        log_not_found off;
    }
    
    # Fichiers robots.txt
    location = /robots.txt {
        access_log off;
        log_not_found off;
    }
    
    # Fichiers statiques Django
    location /static/ {
        alias /var/www/cook/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Fichiers médias
    location /media/ {
        alias /var/www/cook/media/;
        expires 1y;
        add_header Cache-Control "public";
    }
    
    # Reverse proxy vers Gunicorn/Django
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

Activez le site :

```bash
# Créer le lien symbolique
ln -s /etc/nginx/sites-available/cookfamily /etc/nginx/sites-enabled/

# Tester la configuration
nginx -t

# Si OK, recharger Nginx
systemctl reload nginx
```

## 9. Configuration Let's Encrypt SSL

```bash
# Obtenir le certificat SSL
certbot --nginx -d cookfamily.fr -d www.cookfamily.fr

# Le renouvellement automatique est normalement configuré
# Vous pouvez tester avec :
certbot renew --dry-run
```

## 10. Permissions et sécurité

```bash
# Ajuster les permissions
chown -R root:www-data /var/www/cook
chmod -R 755 /var/www/cook
chmod -R 644 /var/www/cook/static
chmod -R 644 /var/www/cook/media

# Sécuriser le fichier .env
chmod 600 /var/www/cook/.env
```

## 11. Configuration du firewall (optionnel mais recommandé)

```bash
# Installation et configuration UFW
apt install ufw

# Règles de base
ufw default deny incoming
ufw default allow outgoing

# Autoriser SSH, HTTP et HTTPS
ufw allow ssh
ufw allow 'Nginx Full'

# Activer le firewall
ufw enable
```

## 12. Scripts de maintenance

Créez un script pour les mises à jour :

```bash
#!/bin/bash
# /var/www/cook/deploy.sh

cd /var/www/cook
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
systemctl restart gunicorn-cook
systemctl reload nginx

echo "Déploiement terminé !"
```

Rendez-le exécutable :

```bash
chmod +x /var/www/cook/deploy.sh
```

## 13. Vérification finale

```bash
# Vérifier que tous les services fonctionnent
systemctl status postgresql
systemctl status gunicorn-cook
systemctl status nginx

# Tester la connectivité
curl -I http://cookfamily.fr
curl -I https://cookfamily.fr
```

## Notes importantes

- Remplacez `votre_mot_de_passe_securise` par un mot de passe fort
- Adaptez les chemins selon votre structure de projet
- Vérifiez que votre DNS pointe bien vers l'IP 31.97.69.141
- Sauvegardez régulièrement votre base de données PostgreSQL
- Surveillez les logs dans `/var/log/nginx/` et avec `journalctl -u gunicorn-cook`