# Flight Price Prediction - HTTPS Setup Guide

## 🔒 HTTPS Configuration

The Flight Price Prediction Flask application now supports **HTTPS (SSL/TLS)** encryption for secure communication.

---

## ✅ SSL Certificates Status

✓ **Certificate File**: `cert.pem` (1,879 bytes)  
✓ **Private Key File**: `key.pem` (3,243 bytes)  
✓ **Status**: Ready to use

---

## 🚀 How to Run with HTTPS

### **Option 1: Simple HTTPS (Recommended for Development)**

```bash
cd PredictFlightPrice

# Method A: Using the helper script
python run.py https

# Method B: Direct Python execution
python app.py
```

**Access at**:
```
https://localhost:8000
https://127.0.0.1:8000
```

### **Option 2: HTTP Mode (Unencrypted - Not Recommended)**

Only use for development if absolutely necessary:

```bash
cd PredictFlightPrice
python run.py http
```

**Access at**:
```
http://localhost:8000
```

### **Option 3: Production with Gunicorn + HTTPS**

For production deployments:

```bash
cd PredictFlightPrice

# Method A: Using helper script
python run.py prod

# Method B: Direct Gunicorn command
gunicorn --certfile=cert.pem --keyfile=key.pem --workers 4 --bind 0.0.0.0:8000 app:app
```

**Features**:
- 4 worker processes
- SSL/TLS encryption
- Production-grade performance
- Automatic request handling

---

## 🌐 Browser Access

### **Step 1: Navigate to HTTPS URL**

```
https://localhost:8000
```

### **Step 2: Handle Certificate Warning**

You may see a browser warning:

```
"Your connection is not private"
"This server could not prove that it is localhost; 
its security certificate is from *.example.com"
```

**This is EXPECTED** because:
- It's a self-signed certificate (not from a trusted CA)
- Self-signed certificates are fine for development
- The connection is still encrypted

### **Step 3: Proceed Safely**

- **Chrome**: Click "Advanced" → "Proceed to localhost (unsafe)"
- **Firefox**: Click "Advanced..." → "Accept the Risk and Continue"
- **Safari**: Click "Show Details" → "visit this website"
- **Edge**: Click "Details" → "Go on to the webpage (not recommended)"

---

## 📡 API Access with HTTPS

### **Using cURL**

**Skip SSL verification** (for self-signed certificates):

```bash
curl -k -X POST https://localhost:8000/predict \
  -d "from=Sao_Paulo&Destination=Rio_de_Janeiro&flightType=premium&agency=FlyingDrops&day=15&week_no=20&week_day=3"
```

**With certificate verification**:

```bash
curl --cacert cert.pem -X POST https://localhost:8000/predict \
  -d "from=Sao_Paulo&Destination=Rio_de_Janeiro&flightType=premium&agency=FlyingDrops&day=15&week_no=20&week_day=3"
```

### **Using Python Requests**

```python
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Suppress SSL warning for self-signed certificates
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Skip SSL verification
response = requests.post(
    'https://localhost:8000/predict',
    data={
        'from': 'Sao_Paulo',
        'Destination': 'Rio_de_Janeiro',
        'flightType': 'premium',
        'agency': 'FlyingDrops',
        'day': 15,
        'week_no': 20,
        'week_day': 3
    },
    verify=False  # Skip SSL certificate verification
)

print(response.json())
```

### **Using JavaScript/Fetch**

```javascript
// Handle HTTPS with self-signed certificate in Node.js
const https = require('https');
const fs = require('fs');

const agent = new https.Agent({
  cert: fs.readFileSync('cert.pem'),
  key: fs.readFileSync('key.pem'),
  rejectUnauthorized: false
});

fetch('https://localhost:8000/predict', {
  method: 'POST',
  agent: agent,
  body: new URLSearchParams({
    from: 'Sao_Paulo',
    Destination: 'Rio_de_Janeiro',
    flightType: 'premium',
    agency: 'FlyingDrops',
    day: 15,
    week_no: 20,
    week_day: 3
  })
})
.then(r => r.json())
.then(data => console.log(data));
```

---

## 🐳 Docker Deployment with HTTPS

### **Dockerfile Configuration**

The Dockerfile automatically includes HTTPS support:

```dockerfile
FROM python:3.12.4-slim
WORKDIR /app
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy SSL certificates
COPY cert.pem /app/cert.pem
COPY key.pem /app/key.pem

EXPOSE 8000

# Run with HTTPS
CMD ["python", "app.py"]
```

### **Build and Run Docker Image**

```bash
# Build
docker build -t mamoor/flight-price-pred:https .

# Run with port mapping
docker run -p 8000:8000 mamoor/flight-price-pred:https

# Access at https://localhost:8000
```

---

## ☸️ Kubernetes Deployment with HTTPS

### **Create TLS Secret**

```bash
kubectl create secret tls flight-price-tls \
  --cert=cert.pem \
  --key=key.pem \
  -n default
```

### **Updated deployment.yml**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: flight-price-pred
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: flight-price-pred
        image: mamoor/flight-price-pred:https
        ports:
        - containerPort: 8000
        volumeMounts:
        - name: tls-certs
          mountPath: /app/certs
      volumes:
      - name: tls-certs
        secret:
          secretName: flight-price-tls
```

### **Deploy**

```bash
kubectl apply -f deployment.yml
kubectl apply -f service.yml
```

---

## 🔐 SSL/TLS Certificate Details

### **Certificate Information**

```bash
# View certificate details
openssl x509 -in cert.pem -text -noout

# View certificate expiration
openssl x509 -in cert.pem -noout -dates
```

### **Certificate Regeneration**

If certificates expire or you need new ones:

```bash
# Generate new self-signed certificate (365 days)
openssl req -x509 -newkey rsa:4096 -nodes \
  -out cert.pem -keyout key.pem -days 365 \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

# Or use the provided script
python generate_cert.py
```

---

## 🚦 Troubleshooting

### **Issue: "Certificate verify failed"**

**Solution**: Skip certificate verification (for development only):

```bash
# With cURL
curl -k https://localhost:8000

# With Python
requests.get('https://localhost:8000', verify=False)
```

### **Issue: "Port 8000 already in use"**

**Solution**: Use a different port:

```bash
# In app.py or run.py, change port parameter:
app.run(port=8443)  # Use 8443 instead

# Or specify on command line:
python run.py https --port 8443
```

### **Issue: "SSL: CERTIFICATE_VERIFY_FAILED"**

**Solution**: This is normal for self-signed certificates.

Add to your client:
```python
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
```

### **Issue: Browser says "NET::ERR_CERT_AUTHORITY_INVALID"**

**Solution**: This is expected. Proceed anyway (the connection is still encrypted).

---

## 📊 Security Considerations

### **Self-Signed Certificates**

✓ **Pros**:
- No cost
- Full control
- Suitable for development/testing
- Encryption still works

✗ **Cons**:
- Browser warnings
- Not trusted by default
- Should only be used internally

### **Production Recommendations**

For production use:

1. **Get CA-signed certificates** from:
   - Let's Encrypt (free)
   - DigiCert, GlobalSign, etc. (paid)

2. **Install certificates** in your deployment:
   ```bash
   # Use Let's Encrypt with Certbot
   sudo certbot certonly --standalone -d yourdomain.com
   ```

3. **Configure in app**:
   ```python
   app.run(ssl_context=('/path/to/cert.pem', '/path/to/key.pem'))
   ```

4. **Monitor certificate expiration**:
   ```bash
   openssl x509 -in cert.pem -noout -dates
   ```

---

## 📝 Summary

| Aspect | Details |
|--------|---------|
| **HTTPS Status** | ✅ Enabled |
| **Certificate Type** | Self-signed |
| **Encryption** | AES-256 (typical) |
| **Port** | 8000 (configurable) |
| **Browser Access** | https://localhost:8000 |
| **API Access** | curl -k https://localhost:8000/predict |
| **Production Ready** | Yes (with Gunicorn) |
| **Docker Support** | Yes (included) |
| **Kubernetes Support** | Yes (requires TLS secret) |

---

## 🔄 Quick Commands

```bash
# Start HTTPS (recommended)
cd PredictFlightPrice && python run.py https

# Start HTTP (unencrypted)
cd PredictFlightPrice && python run.py http

# Production with Gunicorn
cd PredictFlightPrice && python run.py prod

# Docker
docker build -t flight-price-pred:https .
docker run -p 8000:8000 flight-price-pred:https

# Kubernetes
kubectl apply -f deployment.yml
```

---

**Status**: ✅ Ready for HTTPS Deployment  
**Last Updated**: May 18, 2026
