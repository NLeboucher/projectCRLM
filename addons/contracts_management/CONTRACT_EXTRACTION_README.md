# Contract Field Extraction Feature

## Installation / Upgrade

After adding this feature, you need to upgrade the `contracts_management` module in Odoo:

### Option 1: Via Odoo UI
1. Go to **Apps** menu
2. Remove the "Apps" filter to show all modules
3. Search for "Contracts Management"
4. Click the **Upgrade** button (or **Install** if not yet installed)

### Option 2: Via Command Line
```bash
# Restart Odoo with upgrade flag
./odoo-bin -u contracts_management -d your_database_name
```

### Option 3: Via Developer Mode
1. Enable Developer Mode: **Settings → Activate Developer Mode**
2. Go to **Apps → Update Apps List**
3. Search for "Contracts Management"
4. Click **Upgrade**

After upgrading, the new fields and buttons will appear in the Contract Templates interface.

## Overview

This feature uses Claude AI to automatically extract and map fields from contract templates (.docx files) to the structured `contracttype.json` schema.

## How It Works

### 1. Data Model

The `contract.template` model has been extended with the following fields:

- **fields_list** (Text): List of all detected fields with their separators/special characters
- **required_fields** (Text): JSON array of field definitions with validation rules
- **suggested_defaults** (Text): JSON object with default values
- **extraction_status** (Selection): Current extraction status
  - `not_extracted`: Initial state
  - `in_progress`: Extraction is running
  - `extracted`: Successfully extracted
  - `error`: Extraction failed
- **extraction_error** (Text): Error message if extraction failed

### 2. Extraction Process

When you trigger extraction on a contract template:

1. **Read Template**: The system reads the .docx file content from the template's file path
2. **Build Prompt**: Combines the template content with the extraction prompt template from `extract_prompt.md`
3. **Query Claude**: Calls `claude.py` script with the complete prompt
4. **Parse Response**: Extracts JSON from Claude's response (handles markdown code blocks)
5. **Store Results**: Saves the extracted fields data in the model

### 3. Integration with contracttype.json

The extraction uses the schema defined in `contracttype.json` to map fields using dot notation paths:

```
contract.metadata.title
contract.parties.0.name
contract.parties.0.address.street
contract.terms.financial.totalValue
contract.provisions.liability.insurance.minimumCoverage
```

## Usage

### Method 1: From Form View

1. Navigate to **Contracts Management > Contract Templates**
2. Open a template record
3. Click the **"Extract Contract Fields"** button in the header
4. Wait for the extraction to complete
5. View the results in the tabs:
   - **Extracted Fields**: Required fields with validation
   - **Suggested Defaults**: Default values for fields
   - **Fields List**: Complete list of detected fields

### Method 2: Context Menu (Right-click)

1. Navigate to **Contracts Management > Contract Templates**
2. In the list view, select one or more templates
3. Click **Action** menu → **Extract Contract Fields**
4. The extraction will run for all selected templates

### Method 3: Programmatically

```python
template = self.env['contract.template'].browse(template_id)
template.extract_contract_fields()
```

## Extraction Prompt Template

The extraction logic is driven by `addons/contracts_management/extract_prompt.md`, which:

- Instructs Claude on how to identify placeholder fields (e.g., `[field]` or `« field »`)
- Provides the complete contracttype.json schema with available paths
- Defines the expected JSON output format
- Includes examples for required fields and suggested defaults

## Output Format

### Required Fields Example
```json
{
  "requiredFields": [
    {
      "name": "Contract Title",
      "type": "text",
      "jsonPath": "contract.metadata.title",
      "description": "The main title or name of the contract",
      "required": true,
      "validation": {
        "minLength": 5,
        "maxLength": 200
      }
    }
  ]
}
```

### Suggested Defaults Example
```json
{
  "suggestedDefaults": {
    "contract.metadata.status": "draft",
    "contract.metadata.createdDate": "{{TODAY}}",
    "contract.terms.financial.currency": "USD",
    "contract.provisions.disputeResolution.method": "arbitration"
  }
}
```

## Technical Details

### Dependencies

- **python-docx**: For reading .docx file content
- **Claude CLI**: Directly calls `/home/nico/.local/bin/claude`
- **subprocess**: For calling Claude CLI
- **json**: For parsing Claude's JSON responses

### File Locations

- Model: `addons/contracts_management/models/contract_template.py`
- Views: `addons/contracts_management/views/contract_template_views.xml`
- Prompt: `addons/contracts_management/extract_prompt.md`
- Claude CLI: `/home/nico/.local/bin/claude`
- Schema: `contracttype.json` (project root)

### Key Methods

**`_read_docx_content()`**
- Extracts text from .docx files using python-docx
- Returns concatenated paragraph text

**`_get_extraction_prompt(template_content)`**
- Reads the extraction prompt template
- Replaces placeholder with actual template content
- Returns complete prompt for Claude

**`_call_claude(prompt)`**
- Directly calls Claude CLI at `/home/nico/.local/bin/claude`
- Single subprocess (no nested calls)
- 2-minute timeout for long extractions
- Returns Claude's raw response

**`extract_contract_fields()`**
- Main orchestration method
- Updates extraction status
- Handles errors and displays notifications
- Stores results in model fields

## Error Handling

The system handles various error scenarios:

- **File not found**: Template .docx file doesn't exist
- **Claude timeout**: Extraction takes longer than 2 minutes
- **Invalid JSON**: Claude's response can't be parsed
- **Script errors**: claude.py execution failures

Errors are stored in the `extraction_error` field and the status is set to 'error'.

## Future Enhancements

Possible improvements following KISS and YAGNI:

1. **Batch Processing**: Queue system for extracting multiple templates
2. **Validation**: Verify extracted fields match actual template placeholders
3. **Auto-extraction**: Trigger extraction when templates are uploaded
4. **Field Mapping UI**: Visual interface to adjust field mappings
5. **Template Versioning**: Track changes to extracted fields over time

## Troubleshooting

### Extraction Status Stuck at "In Progress"
- Check if Claude CLI is accessible at `/home/nico/.local/bin/claude`
- Verify Claude CLI has execute permissions: `chmod +x /home/nico/.local/bin/claude`
- Check Odoo logs for error messages

### Empty Extraction Results
- Ensure the template has recognizable placeholder fields
- Check that extract_prompt.md exists and is readable
- Verify Claude is returning valid JSON

### Permission Errors
- Ensure Odoo has read access to Contrats_template/ directory
- Verify Claude CLI has execute permissions
- Check file system permissions on template files
