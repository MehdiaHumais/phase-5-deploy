# Troubleshooting Guide for Todo Chatbot Setup

This guide provides solutions to common issues you might encounter during the setup process.

## Common Installation Issues

### Git Issues

**Problem**: Git command not found
**Solution**:
- Windows: Reinstall Git and ensure it's added to PATH
- macOS: Install Xcode Command Line Tools: `xcode-select --install`
- Linux: Install Git: `sudo apt install git` (Ubuntu) or `sudo dnf install git` (Fedora)

**Problem**: Permission denied when cloning repository
**Solution**:
- Check your SSH keys if using SSH URLs
- Use HTTPS URL instead: `https://github.com/your-org/todo-chatbot.git`
- Ensure you have access rights to the repository

### Python Issues

**Problem**: Python command not found
**Solution**:
- Install Python 3.9+ from python.org
- Add Python to your system PATH
- Use `python3` instead of `python` on some systems

**Problem**: Permission denied when installing packages
**Solution**:
- Use virtual environment: `python -m venv venv && source venv/bin/activate` (Linux/macOS) or `python -m venv venv && venv\Scripts\activate` (Windows)
- Or use `pip install --user` to install to user directory

**Problem**: Package installation fails
**Solution**:
- Upgrade pip: `pip install --upgrade pip`
- Check for conflicting dependencies
- Clear pip cache: `pip cache purge`

### Node.js Issues

**Problem**: Node.js or npm command not found
**Solution**:
- Install Node.js LTS from nodejs.org
- Add Node.js to your system PATH
- Restart terminal after installation

**Problem**: Permission errors with npm
**Solution**:
- Use a Node version manager like nvm
- Change npm's default directory: `mkdir ~/.npm-global && npm config set prefix '~/.npm-global'`
- Add `~/.npm-global/bin` to your PATH

### Docker Issues

**Problem**: Docker daemon not running
**Solution**:
- Start Docker Desktop application
- On Linux: `sudo systemctl start docker`
- Ensure Docker is set to start on boot

**Problem**: Permission denied when running Docker
**Solution**:
- Add user to docker group: `sudo usermod -aG docker $USER`
- Log out and log back in
- Or run with sudo (not recommended for development)

**Problem**: Docker containers failing to start
**Solution**:
- Check Docker logs: `docker logs <container-name>`
- Ensure sufficient system resources (RAM, disk space)
- Restart Docker service

### Dapr Issues

**Problem**: Dapr CLI not found
**Solution**:
- Verify installation: `dapr --version`
- Add Dapr to PATH if installed manually
- Reinstall using the official installation method

**Problem**: Dapr init fails
**Solution**:
- Ensure Docker is running
- Clear Dapr installation: `dapr uninstall --all`
- Reinitialize: `dapr init`

**Problem**: Dapr sidecar not connecting
**Solution**:
- Check if Dapr placement service is running
- Verify Dapr runtime version compatibility
- Check firewall settings

### Kubernetes Issues

**Problem**: kubectl command not found
**Solution**:
- Install kubectl following official documentation
- Add kubectl to PATH
- Verify installation: `kubectl version --client`

**Problem**: Minikube won't start
**Solution**:
- Check virtualization support in BIOS/UEFI settings
- Try different drivers: `minikube start --driver=docker`
- Clear Minikube: `minikube delete`

## Platform-Specific Issues

### Windows Issues

**Problem**: WSL 2 not available or not working
**Solution**:
- Enable WSL feature: `wsl --install`
- Update WSL kernel: `wsl --update`
- Check Windows version compatibility

**Problem**: Permission issues with file sharing
**Solution**:
- Use Git Bash or Windows Subsystem for Linux
- Check file permissions in the project directory
- Disable Windows Defender real-time scanning for project directory (temporarily)

### macOS Issues

**Problem**: Command Line Tools not found
**Solution**:
- Install with: `xcode-select --install`
- Or install full Xcode from App Store

**Problem**: Homebrew permission issues
**Solution**:
- Fix ownership: `sudo chown -R $(whoami) $(brew --prefix)/*`
- Or reinstall Homebrew

### Linux Issues

**Problem**: Docker group not available
**Solution**:
- Create docker group: `sudo groupadd docker`
- Add user to group: `sudo usermod -aG docker $USER`
- Log out and log back in

**Problem**: Insufficient privileges for some commands
**Solution**:
- Use sudo for system-level commands when necessary
- Configure passwordless sudo for specific commands if needed for development

## Network and Connectivity Issues

**Problem**: Cannot pull Docker images
**Solution**:
- Check internet connectivity
- Verify Docker Hub access
- Try using a different network or VPN if behind corporate firewall

**Problem**: Kafka connection issues
**Solution**:
- Ensure Kafka container is running: `docker ps | grep kafka`
- Check Kafka logs: `docker logs <kafka-container>`
- Verify network connectivity between containers

**Problem**: Application cannot connect to database
**Solution**:
- Verify database container is running
- Check database connection string
- Ensure database migration has run successfully

## Performance Issues

**Problem**: Slow startup times
**Solution**:
- Ensure sufficient system resources (RAM, CPU)
- Close unnecessary applications
- Increase Docker resources in Docker Desktop settings

**Problem**: High memory usage
**Solution**:
- Monitor resource usage with system tools
- Adjust container resource limits
- Close unused containers and services

## Validation and Testing Issues

**Problem**: Setup validation fails
**Solution**:
- Check each component individually
- Verify environment variables are set correctly
- Review logs for specific error messages

**Problem**: Tests failing after setup
**Solution**:
- Ensure all services are running
- Check test configuration
- Run tests individually to isolate the issue

## Getting Help

If you encounter an issue not covered in this guide:

1. Check the application logs in the console output
2. Review Docker logs: `docker logs <container-name>`
3. Check system logs for platform-specific issues
4. Consult the official documentation for each component:
   - [Docker Documentation](https://docs.docker.com/)
   - [Kubernetes Documentation](https://kubernetes.io/docs/)
   - [Dapr Documentation](https://docs.dapr.io/)
   - [Python Documentation](https://docs.python.org/)
   - [Node.js Documentation](https://nodejs.org/docs/)

5. Reach out to the development team with:
   - Detailed description of the issue
   - Steps to reproduce
   - System information (OS, versions of tools)
   - Error messages and logs

## Useful Commands for Troubleshooting

```bash
# Check if services are running
docker ps

# Check logs of a specific container
docker logs <container-name>

# Check system resources
docker stats

# Check Dapr status
dapr status -k

# Check Kubernetes cluster status
kubectl cluster-info

# Check Minikube status
minikube status

# Validate Python environment
python -m pip list

# Validate Node.js environment
npm list
```

## Prevention Tips

1. Regularly update your development tools
2. Keep system resources sufficient for development workloads
3. Use version control to track configuration changes
4. Maintain clean project environments
5. Document custom configurations for reproducibility