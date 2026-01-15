# Security Policy

## ⚠️ Important Security Notice

This setup is designed for **local development and training purposes only**. It is **NOT** production-ready and contains several security configurations that should be changed for production use.

## 🔒 Security Considerations

### Default Credentials

The following default credentials are used and should be changed for any non-local deployment:

**MinIO:**
- Username: `admin`
- Password: `password`

**Recommendation:** Use strong, unique passwords and store them securely (e.g., using environment variables or secrets management).

### Authentication Disabled

**Nessie** has authentication disabled for ease of use in training:
```yaml
QUARKUS_OIDC_ENABLED=false
NESSIE_SERVER_AUTHENTICATION_ENABLED=false
```

**Recommendation:** Enable authentication for any deployment accessible from outside localhost.

### Network Exposure

All services expose ports on `0.0.0.0` (all interfaces):
- Dremio: 9047, 31010, 32010
- MinIO: 9000, 9001
- Nessie: 19120

**Recommendation:** For production, use a reverse proxy (nginx, Traefik) with TLS/SSL and restrict access.

### No TLS/SSL

All communication is unencrypted HTTP.

**Recommendation:** Use HTTPS with valid certificates for production deployments.

### Docker Socket Access

This setup does not require Docker socket access, which is good for security.

## 🛡️ Best Practices for Production

If you want to use this setup as a base for production:

1. **Change all default credentials**
   ```bash
   # Use strong passwords
   MINIO_ROOT_PASSWORD=$(openssl rand -base64 32)
   ```

2. **Enable authentication**
   - Configure Nessie with OIDC or basic auth
   - Use MinIO with IAM policies

3. **Use TLS/SSL**
   - Configure certificates for all services
   - Use Let's Encrypt for public deployments

4. **Restrict network access**
   - Use firewall rules
   - Implement network policies
   - Use VPN for remote access

5. **Use secrets management**
   - Docker secrets
   - Kubernetes secrets
   - HashiCorp Vault
   - Cloud provider secret managers

6. **Regular updates**
   - Pin specific versions instead of `:latest`
   - Regularly update to patch security vulnerabilities

7. **Resource limits**
   - Set CPU and memory limits
   - Implement rate limiting

8. **Monitoring and logging**
   - Enable audit logging
   - Monitor for suspicious activity
   - Set up alerts

## 🐛 Reporting Security Issues

If you discover a security vulnerability in this setup:

1. **Do NOT** open a public issue
2. Email the maintainer privately
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

## 📋 Security Checklist for Production

- [ ] Changed all default passwords
- [ ] Enabled authentication on all services
- [ ] Configured TLS/SSL certificates
- [ ] Restricted network access
- [ ] Implemented secrets management
- [ ] Pinned specific image versions
- [ ] Set resource limits
- [ ] Enabled audit logging
- [ ] Configured backups
- [ ] Set up monitoring and alerts
- [ ] Reviewed and hardened Docker configurations
- [ ] Implemented least privilege access

## 📚 Additional Resources

- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [MinIO Security](https://min.io/docs/minio/linux/operations/security.html)
- [Nessie Security](https://projectnessie.org/nessie-latest/configuration/#authentication-settings)
- [Dremio Security](https://docs.dremio.com/current/security/)

## ⚖️ Disclaimer

This project is provided "as is" for educational purposes. The maintainers are not responsible for any security issues arising from the use of this setup in production environments.

