import os
import json
import subprocess
from odoo import models, fields, api
from docx import Document


class ContractTemplate(models.Model):
    _name = 'contract.template'
    _description = 'Contract Template'
    _rec_name = 'name'

    name = fields.Char(string='Template Name', required=True)
    file_path = fields.Char(string='File Path', required=True)
    template_type = fields.Char(string='Template Type')
    
    # Contract extraction fields
    fields_list = fields.Text(string='Extracted Fields', help='List of all detected fields with separators')
    required_fields = fields.Text(string='Required Fields', help='JSON array of field definitions with validation rules')
    suggested_defaults = fields.Text(string='Suggested Defaults', help='JSON object with default values')
    extraction_status = fields.Selection([
        ('not_extracted', 'Not Extracted'),
        ('in_progress', 'In Progress'),
        ('extracted', 'Extracted'),
        ('error', 'Error')
    ], string='Extraction Status', default='not_extracted')
    extraction_error = fields.Text(string='Extraction Error')
    
    @api.model
    def _get_templates_directory(self):
        """Get the path to the Contrats_template directory"""
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        return os.path.join(base_path, 'Contrats_template')
    
    @api.model
    def refresh_templates(self):
        """Scan the Contrats_template directory and create/update records"""
        templates_dir = self._get_templates_directory()
        
        if not os.path.exists(templates_dir):
            return
        
        # Get all .docx files
        existing_files = set()
        for filename in os.listdir(templates_dir):
            if filename.endswith('.docx'):
                file_path = os.path.join(templates_dir, filename)
                existing_files.add(file_path)
                
                # Check if template already exists
                template = self.search([('file_path', '=', file_path)], limit=1)
                
                if not template:
                    # Create new template record
                    template_name = os.path.splitext(filename)[0].replace('_', ' ')
                    self.create({
                        'name': template_name,
                        'file_path': file_path,
                        'template_type': self._get_template_type(template_name),
                    })
        
        # Remove records for files that no longer exist
        all_templates = self.search([])
        for template in all_templates:
            if template.file_path not in existing_files:
                template.unlink()
    # TODO BUILD MORE MODEL TYPES MAYBE BE GENERALIZE
    def _get_template_type(self, name):
        """Determine template type from name"""
        name_lower = name.lower()
        if 'vente' in name_lower or 'sale' in name_lower:
            return 'Sales Contract'
        elif 'travail' in name_lower or 'employment' in name_lower:
            if 'déterminée' in name_lower or 'fixed' in name_lower:
                return 'Fixed-term Employment'
            elif 'indéterminée' in name_lower or 'permanent' in name_lower:
                return 'Permanent Employment'
            return 'Employment Contract'
        return 'General Contract'
    
    def _read_docx_content(self):
        """Extract text content from .docx file"""
        if not os.path.exists(self.file_path):
            raise Exception(f"Template file not found: {self.file_path}")
        
        doc = Document(self.file_path)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        return '\n'.join(full_text)
    
    def _get_extraction_prompt(self, template_content):
        """Build the complete extraction prompt"""
        # Read the extraction prompt template
        prompt_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'extract_prompt.md'
        )
        
        with open(prompt_path, 'r', encoding='utf-8') as f:
            prompt_template = f.read()
        
        # Replace the placeholder with actual template content
        return prompt_template.replace('[INSERT RAW TEXT FROM TEMPLATE HERE]', template_content)
    
    def _call_claude(self, prompt):
        """Call Claude CLI directly"""
        claude_cli_path = '/home/nico/.local/bin/claude'
        
        try:
            result = subprocess.run(
                [claude_cli_path, '-p', '--dangerously-skip-permissions'],  # Bypass permission checks for automated environment
                input=prompt,              # Pass prompt via stdin (no size limit)
                capture_output=True,
                text=True,
                check=True,
                timeout=120,  # 2 minute timeout
                env=os.environ.copy()  # Pass environment variables
            )
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            raise Exception("Claude query timed out after 2 minutes")
        except subprocess.CalledProcessError as e:
            error_msg = f"Error calling Claude CLI: Return code {e}"
            if e.stdout:
                error_msg += f"\nStdout: {e.stdout}"
            if e.stderr:
                error_msg += f"\nStderr: {e.stderr}"
            raise Exception(error_msg)
        except FileNotFoundError:
            raise Exception(f"Claude CLI not found at {claude_cli_path}. Please ensure Claude Code is installed.")
    
    def extract_contract_fields(self):
        """Extract contract fields using Claude AI"""
        self.ensure_one()
        
        try:
            # Update status
            self.write({
                'extraction_status': 'in_progress',
                'extraction_error': False
            })
            
            # Read template content
            template_content = self._read_docx_content()
            
            # Build the prompt
            prompt = self._get_extraction_prompt(template_content)
            
            # Call Claude
            response = self._call_claude(prompt)
            
            # Parse the JSON response
            # Extract JSON from response (Claude might wrap it in markdown code blocks)
            if '```json' in response:
                json_start = response.find('```json') + 7
                json_end = response.find('```', json_start)
                json_str = response[json_start:json_end].strip()
            elif '```' in response:
                json_start = response.find('```') + 3
                json_end = response.find('```', json_start)
                json_str = response[json_start:json_end].strip()
            else:
                json_str = response.strip()
            
            extracted_data = json.loads(json_str)
            
            # Store the extracted data
            self.write({
                'required_fields': json.dumps(extracted_data.get('requiredFields', []), indent=2),
                'suggested_defaults': json.dumps(extracted_data.get('suggestedDefaults', {}), indent=2),
                'fields_list': json.dumps(extracted_data.get('fields', []), indent=2) if 'fields' in extracted_data else '',
                'extraction_status': 'extracted',
                'extraction_error': False
            })
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Success',
                    'message': f'Successfully extracted fields from {self.name}',
                    'type': 'success',
                    'sticky': False,
                }
            }
            
        except Exception as e:
            self.write({
                'extraction_status': 'error',
                'extraction_error': str(e)
            })
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'message': f'Failed to extract fields: {str(e)}',
                    'type': 'danger',
                    'sticky': True,
                }
            }
