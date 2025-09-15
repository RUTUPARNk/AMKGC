# Neo4j Setup Guide

## Overview
This guide provides instructions for setting up Neo4j for the Node-LLM System. You can choose from three options:

1. Using Docker (recommended for development)
2. Installing Neo4j Desktop (recommended for local development)
3. Using a remote Neo4j instance (recommended for production)

## Option 1: Using Docker (Recommended for Development)

### Prerequisites
- Docker installed and running
- Docker Compose

### Steps
1. Ensure Docker is running on your system
2. Navigate to the project root directory
3. Run the following command:
   ```bash
   docker-compose -f docker-compose-neo4j.yaml up -d
   ```
4. Wait for the container to start (usually 30-60 seconds)
5. Verify the container is running:
   ```bash
   docker-compose -f docker-compose-neo4j.yaml ps
   ```

### Troubleshooting Docker Issues
If you encounter issues with Docker:

1. Make sure Docker Desktop is installed and running
2. Check if Docker is using WSL2 backend (required on Windows)
3. Ensure no other service is using ports 7474 or 7687
4. Try restarting Docker Desktop

## Option 2: Neo4j Desktop (Alternative for Local Development)

### Steps
1. Download and install Neo4j Desktop from https://neo4j.com/download/
2. Create a new project
3. Add a new database (choose Neo4j 5.x version)
4. Set the password to "password" (to match default configuration)
5. Start the database
6. Install the APOC plugin:
   - Go to the "Plugins" tab
   - Click "Install" next to APOC
7. Update your `.env` file to use the correct connection details

## Option 3: Remote Neo4j Instance

### Steps
1. Obtain connection details for your remote Neo4j instance
2. Update the `.env` file with the correct connection parameters:
   ```env
   NEO4J_URI=bolt://your-neo4j-host:7687
   NEO4J_USER=your-username
   NEO4J_PASSWORD=your-password
   ```

## Environment Configuration

The system uses the following environment variables for Neo4j connection:

- `NEO4J_URI` - Connection URI (default: bolt://localhost:7687)
- `NEO4J_USER` - Username (default: neo4j)
- `NEO4J_PASSWORD` - Password (default: password)

## Testing the Connection

After setting up Neo4j, run the test script to verify the connection:

```bash
python test_neo4j_simple.py
```

## Common Issues and Solutions

### Connection Refused
- Ensure Neo4j is running
- Check if the correct ports are being used (7687 for Bolt, 7474 for HTTP)
- Verify firewall settings

### Authentication Failed
- Ensure the username and password match your Neo4j instance
- For Neo4j 5.x, the default username is "neo4j"
- Reset the password if needed

### Docker Issues
- Make sure Docker is running
- Check if Docker has enough resources (memory, CPU)
- Verify that the required ports are available

## Next Steps

Once Neo4j is running:
1. Run the migration script to transfer existing data:
   ```bash
   python backend/scripts/migrate_to_neo4j.py
   ```
2. Test the integration with the full test suite:
   ```bash
   python test_neo4j_integration.py
   ```
