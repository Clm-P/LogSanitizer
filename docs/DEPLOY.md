# LogSanitizer — Deployment Guide

This guide covers a full production deployment of LogSanitizer on Apache with HTTPS.  
Two distribution families are covered: **RHEL / CentOS** and **Debian / Ubuntu**.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Prerequisites](#2-prerequisites)
3. [File Structure](#3-file-structure)
4. [RHEL / CentOS Deployment](#4-rhel--centos-deployment)
5. [Debian / Ubuntu Deployment](#5-debian--ubuntu-deployment)
6. [Apache Virtual Host Configuration](#6-apache-virtual-host-configuration)
7. [File Permissions](#7-file-permissions)
8. [SSL Certificate](#8-ssl-certificate)
9. [Verification](#9-verification)
10. [Updating Rules or Profiles](#10-updating-rules-or-profiles)

---

## 1. Overview

LogSanitizer is a static single-page application served by Apache. There is no database and no application server. The only dynamic component is a pair of Python CGI scripts (`api/rules.py`, `api/profiles.py`) that allow the app to persist custom user-created rules and profiles to the server.

```
Browser  ──HTTPS──►  Apache  ──static──►  index.html
                              ──static──►  data/shared-*.json
                              ──CGI────►  api/rules.py
                              ──CGI────►  api/profiles.py
                                            │
                                            └──► data/custom-*.json  (writable)
```

---

## 2. Prerequisites

| Requirement | RHEL / CentOS | Debian / Ubuntu |
|---|---|---|
| Web server | `httpd` | `apache2` |
| SSL module | `mod_ssl` | `mod_ssl` (built-in) |
| Python | `python3` | `python3` |
| Firewall | `firewalld` | `ufw` |
| SELinux | Yes (enforcing by default) | No (AppArmor, minimal impact) |

A valid SSL certificate and key are required for HTTPS. Self-signed certificates work for internal deployments — see [Section 8](#8-ssl-certificate).

---

## 3. File Structure

After deployment, the docroot should contain:

```
/var/www/logsanitizer/
├── index.html                  # Application (read-only)
├── data/
│   ├── shared-rules.json       # Admin-managed rules (read-only)
│   ├── shared-profiles.json    # Admin-managed profiles (read-only)
│   ├── custom-rules.json       # User rules written by CGI (writable by Apache)
│   └── custom-profiles.json    # User profiles written by CGI (writable by Apache)
└── api/
    ├── rules.py                # CGI script — saves custom rules
    └── profiles.py             # CGI script — saves custom profiles
```

---

## 4. RHEL / CentOS Deployment

Tested on CentOS Stream 9 and RHEL 9. Steps are identical for both.

### 4.1 Install packages

```bash
sudo dnf install -y httpd mod_ssl python3
```

### 4.2 Copy application files

```bash
sudo mkdir -p /var/www/logsanitizer/data /var/www/logsanitizer/api

sudo cp index.html            /var/www/logsanitizer/
sudo cp data/shared-rules.json    /var/www/logsanitizer/data/
sudo cp data/shared-profiles.json /var/www/logsanitizer/data/
sudo cp data/custom-rules.json    /var/www/logsanitizer/data/
sudo cp data/custom-profiles.json /var/www/logsanitizer/data/
sudo cp api/rules.py              /var/www/logsanitizer/api/
sudo cp api/profiles.py           /var/www/logsanitizer/api/
```

### 4.3 Set permissions

```bash
# Ownership
sudo chown -R apache:apache /var/www/logsanitizer/

# Static files and scripts — read-only for Apache
sudo chmod 644 /var/www/logsanitizer/index.html
sudo chmod 644 /var/www/logsanitizer/data/shared-rules.json
sudo chmod 644 /var/www/logsanitizer/data/shared-profiles.json

# CGI scripts — must be executable
sudo chmod 755 /var/www/logsanitizer/api/rules.py
sudo chmod 755 /var/www/logsanitizer/api/profiles.py

# Custom data files — writable by Apache (CGI writes here)
sudo chmod 664 /var/www/logsanitizer/data/custom-rules.json
sudo chmod 664 /var/www/logsanitizer/data/custom-profiles.json
sudo chmod 775 /var/www/logsanitizer/data/
```

### 4.4 SELinux configuration

SELinux is enforcing by default on RHEL/CentOS and will block CGI execution and file writes without the correct contexts.

```bash
# Allow Apache to serve CGI scripts from the docroot
sudo semanage fcontext -a -t httpd_sys_script_exec_t \
    "/var/www/logsanitizer/api(/.*)?"
sudo restorecon -Rv /var/www/logsanitizer/api/

# Allow Apache to write to the data directory
sudo semanage fcontext -a -t httpd_sys_rw_content_t \
    "/var/www/logsanitizer/data(/.*)?"
sudo restorecon -Rv /var/www/logsanitizer/data/

# Verify contexts
ls -Z /var/www/logsanitizer/api/
ls -Z /var/www/logsanitizer/data/
```

> If `semanage` is not found, install it: `sudo dnf install -y policycoreutils-python-utils`

### 4.5 Firewall

```bash
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

If HTTP-to-HTTPS redirect is needed:

```bash
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --reload
```

### 4.6 Place the virtual host config and enable Apache

```bash
# Place the vhost file (see Section 6)
sudo vi /etc/httpd/conf.d/logsanitizer.conf

# Test configuration
sudo apachectl configtest

# Enable and start
sudo systemctl enable --now httpd
```

---

## 5. Debian / Ubuntu Deployment

Tested on Ubuntu 22.04 LTS and Debian 12.

### 5.1 Install packages

```bash
sudo apt update
sudo apt install -y apache2 python3
```

### 5.2 Enable required Apache modules

```bash
sudo a2enmod ssl cgid headers
sudo systemctl restart apache2
```

> `cgid` is the recommended CGI daemon module for multi-threaded MPMs (the default on Debian/Ubuntu). Use `cgi` instead if running the prefork MPM.

### 5.3 Copy application files

```bash
sudo mkdir -p /var/www/logsanitizer/data /var/www/logsanitizer/api

sudo cp index.html                    /var/www/logsanitizer/
sudo cp data/shared-rules.json        /var/www/logsanitizer/data/
sudo cp data/shared-profiles.json     /var/www/logsanitizer/data/
sudo cp data/custom-rules.json        /var/www/logsanitizer/data/
sudo cp data/custom-profiles.json     /var/www/logsanitizer/data/
sudo cp api/rules.py                  /var/www/logsanitizer/api/
sudo cp api/profiles.py               /var/www/logsanitizer/api/
```

### 5.4 Set permissions

```bash
# Ownership (www-data on Debian/Ubuntu)
sudo chown -R www-data:www-data /var/www/logsanitizer/

# Static files
sudo chmod 644 /var/www/logsanitizer/index.html
sudo chmod 644 /var/www/logsanitizer/data/shared-rules.json
sudo chmod 644 /var/www/logsanitizer/data/shared-profiles.json

# CGI scripts — must be executable
sudo chmod 755 /var/www/logsanitizer/api/rules.py
sudo chmod 755 /var/www/logsanitizer/api/profiles.py

# Custom data files — writable by Apache
sudo chmod 664 /var/www/logsanitizer/data/custom-rules.json
sudo chmod 664 /var/www/logsanitizer/data/custom-profiles.json
sudo chmod 775 /var/www/logsanitizer/data/
```

### 5.5 Firewall

```bash
sudo ufw allow 443/tcp
sudo ufw reload
```

If HTTP-to-HTTPS redirect is needed:

```bash
sudo ufw allow 80/tcp
sudo ufw reload
```

### 5.6 Place the virtual host config and enable the site

```bash
# Place the vhost file (see Section 6)
sudo vi /etc/apache2/sites-available/logsanitizer.conf

# Enable the site
sudo a2ensite logsanitizer.conf

# Test configuration
sudo apachectl configtest

# Reload Apache
sudo systemctl reload apache2
```

---

## 6. Apache Virtual Host Configuration

The configuration is the same for both distributions. Adjust `ServerName` and certificate paths to match your environment.

```apache
<VirtualHost *:443>
    ServerName logsanitizer.corp.internal
    DocumentRoot /var/www/logsanitizer

    # SSL
    SSLEngine on
    SSLCertificateFile    /etc/pki/tls/certs/logsanitizer.crt
    SSLCertificateKeyFile /etc/pki/tls/private/logsanitizer.key
    # SSLCertificateChainFile /etc/pki/tls/certs/ca-bundle.crt  # if using a CA chain

    # Main docroot
    <Directory /var/www/logsanitizer>
        Options -Indexes
        AllowOverride None
        Require all granted
    </Directory>

    # CGI API — enable script execution for api/ only
    <Directory /var/www/logsanitizer/api>
        Options +ExecCGI
        AddHandler cgi-script .py
        Require all granted
    </Directory>

    # Prevent direct access to data/ from outside
    <Directory /var/www/logsanitizer/data>
        Options -Indexes
        Require all granted
    </Directory>

    # Cache-control: force revalidation of shared data files
    <LocationMatch "^/data/.*\.json$">
        Header set Cache-Control "no-cache, must-revalidate"
    </LocationMatch>

    # Logging
    ErrorLog  /var/log/httpd/logsanitizer-error.log   # RHEL/CentOS
    CustomLog /var/log/httpd/logsanitizer-access.log combined
    # ErrorLog  /var/log/apache2/logsanitizer-error.log  # Debian/Ubuntu
    # CustomLog /var/log/apache2/logsanitizer-access.log combined
</VirtualHost>

# Optional: redirect HTTP to HTTPS
<VirtualHost *:80>
    ServerName logsanitizer.corp.internal
    Redirect permanent / https://logsanitizer.corp.internal/
</VirtualHost>
```

---

## 7. File Permissions

Summary of expected permissions after setup:

| Path | Owner | Mode | Reason |
|---|---|---|---|
| `index.html` | apache / www-data | `644` | Read-only static file |
| `data/shared-rules.json` | apache / www-data | `644` | Read-only, admin-managed |
| `data/shared-profiles.json` | apache / www-data | `644` | Read-only, admin-managed |
| `data/custom-rules.json` | apache / www-data | `664` | Written by CGI |
| `data/custom-profiles.json` | apache / www-data | `664` | Written by CGI |
| `data/` | apache / www-data | `775` | CGI needs write access |
| `api/rules.py` | apache / www-data | `755` | Must be executable for CGI |
| `api/profiles.py` | apache / www-data | `755` | Must be executable for CGI |

---

## 8. SSL Certificate

### Option A — Internal CA or existing certificate

Copy your certificate and key to the paths referenced in the vhost:

```bash
# RHEL / CentOS
sudo cp logsanitizer.crt /etc/pki/tls/certs/logsanitizer.crt
sudo cp logsanitizer.key /etc/pki/tls/private/logsanitizer.key
sudo chmod 644 /etc/pki/tls/certs/logsanitizer.crt
sudo chmod 600 /etc/pki/tls/private/logsanitizer.key

# Debian / Ubuntu
sudo cp logsanitizer.crt /etc/ssl/certs/logsanitizer.crt
sudo cp logsanitizer.key /etc/ssl/private/logsanitizer.key
sudo chmod 644 /etc/ssl/certs/logsanitizer.crt
sudo chmod 640 /etc/ssl/private/logsanitizer.key
```

Update `SSLCertificateFile` and `SSLCertificateKeyFile` in the vhost accordingly.

### Option B — Self-signed certificate (internal / air-gapped)

```bash
sudo openssl req -x509 -nodes -days 3650 -newkey rsa:4096 \
    -keyout /etc/pki/tls/private/logsanitizer.key \
    -out    /etc/pki/tls/certs/logsanitizer.crt \
    -subj   "/CN=logsanitizer.corp.internal" \
    -addext "subjectAltName=DNS:logsanitizer.corp.internal"
```

> For Debian/Ubuntu, replace the paths with `/etc/ssl/private/` and `/etc/ssl/certs/`.

Distribute the `.crt` to browsers or the system trust store so users do not see certificate warnings.

---

## 9. Verification

### 9.1 Check Apache is running

```bash
# RHEL / CentOS
sudo systemctl status httpd

# Debian / Ubuntu
sudo systemctl status apache2
```

### 9.2 Test the application

```bash
# Should return 200 and the HTML page
curl -sk https://logsanitizer.corp.internal/ | grep -c "LogSanitizer"

# Should return the shared rules JSON
curl -sk https://logsanitizer.corp.internal/data/shared-rules.json | python3 -m json.tool > /dev/null && echo "OK"

# Should return 405 (CGI reachable, rejects GET as expected)
curl -sk -o /dev/null -w "%{http_code}" \
    https://logsanitizer.corp.internal/api/rules.py
```

### 9.3 Test the CGI write path

```bash
# POST a valid rules array — should return {"success": true}
curl -sk -X POST \
    -H "Content-Type: application/json" \
    -d "$(cat /var/www/logsanitizer/data/custom-rules.json)" \
    https://logsanitizer.corp.internal/api/rules.py
```

### 9.4 Check logs

```bash
# RHEL / CentOS
sudo tail -f /var/log/httpd/logsanitizer-error.log

# Debian / Ubuntu
sudo tail -f /var/log/apache2/logsanitizer-error.log
```

---

## 10. Updating Rules or Profiles

Shared rules and profiles are plain JSON files. No Apache restart is required after editing them — users pick up changes on their next page load.

```bash
# Edit
sudo vi /var/www/logsanitizer/data/shared-rules.json

# Validate JSON syntax before saving
python3 -m json.tool /var/www/logsanitizer/data/shared-rules.json > /dev/null \
    && echo "JSON valid" || echo "JSON invalid — fix before saving"
```
