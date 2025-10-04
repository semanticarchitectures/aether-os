# Aether OS OPA Policies

This directory contains Open Policy Agent (OPA) policies for Aether OS authorization.

## Policy Files

- `agent_authorization.rego` - Main authorization policies for agent actions
- `phase_constraints.rego` - Phase-based access restrictions
- `test_policies.rego` - Policy unit tests

## Running OPA Server

To run the OPA server for development:

```bash
# Install OPA
brew install opa  # macOS
# or
wget https://openpolicyagent.org/downloads/latest/opa_linux_amd64 -O opa

# Run OPA server
opa run --server --addr localhost:8181 policies/
```

## Testing Policies

```bash
# Run policy tests
opa test policies/
```

## Policy Structure

Policies are organized under the `aether` package with the following modules:

- `aether.agent_authorization` - Agent action authorization
- `aether.phase_constraints` - Phase-based restrictions

## Example Query

```bash
# Check if spectrum manager can allocate frequency in Phase 3
curl -X POST http://localhost:8181/v1/data/aether/agent_authorization/allow \
  -d '{
    "input": {
      "agent": {
        "role": "spectrum_manager",
        "access_level": 3
      },
      "action": {
        "type": "allocate_frequency"
      },
      "ato_cycle": {
        "current_phase": "PHASE3_WEAPONEERING"
      }
    }
  }'
```
