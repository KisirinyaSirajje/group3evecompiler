"""
EveCompiler Web UI — Flask Server
Provides a web interface for compiling mini-C code
"""

from flask import Flask, render_template, request, jsonify
import json
import os
import sys
from pathlib import Path

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

try:
    from cli import compile_source, ast_to_json
except ImportError as e:
    print(f"ERROR: Cannot import cli: {e}")
    sys.exit(1)

# Create Flask app with proper paths
app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, 'templates'),
    static_folder=os.path.join(BASE_DIR, 'static'),
    static_url_path='/static'
)

# Configure Flask
app.config['JSON_SORT_KEYS'] = False
app.url_map.strict_slashes = False


@app.route('/', methods=['GET'])
def index():
    """Serve the main IDE page"""
    try:
        print(f"[LOG] Rendering index.html from {app.template_folder}")
        return render_template('index.html')
    except Exception as e:
        print(f"[ERROR] Failed to render template: {e}")
        import traceback
        traceback.print_exc()
        return f"<h1>Error Loading Page</h1><p>{str(e)}</p><pre>{traceback.format_exc()}</pre>", 500


@app.route('/api/compile', methods=['POST'])
def compile_api():
    """API endpoint for compilation"""
    try:
        data = request.json
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
            
        source_code = data.get('code', '')
        
        if not source_code.strip():
            return jsonify({
                'success': False,
                'error': 'No source code provided'
            })
        
        result = compile_source(source_code, verbose=False)
        
        # Format output
        response = {
            'success': result['success'],
            'phase': result['phase'],
            'error': result['error']
        }
        
        if result['success']:
            response['statistics'] = {
                'tokens': len(result['tokens']),
                'ir_lines': len(result['ir']),
                'assembly_lines': len(result['assembly'])
            }
            
            response['symbol_table'] = result['symbol_table']
            response['tokens'] = [{'type': t[0], 'value': t[1]} for t in result['tokens']]
            response['assembly'] = result['assembly']
            response['optimized_ir'] = result['optimized_ir']
            response['ast_tree'] = ast_to_json(result['ast'])
        
        return jsonify(response)
    
    except Exception as e:
        print(f"[ERROR] Compilation failed: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500


@app.route('/api/samples', methods=['GET'])
def get_samples():
    """Get available sample programs"""
    try:
        samples_dir = Path(BASE_DIR) / 'sample_programs'
        
        samples = {}
        if samples_dir.exists():
            for file in samples_dir.glob('*.c'):
                try:
                    with open(file, 'r') as f:
                        samples[file.stem] = f.read()
                except Exception as e:
                    print(f'[ERROR] Error reading {file}: {e}')
        
        return jsonify(samples)
    except Exception as e:
        print(f"[ERROR] Samples endpoint failed: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/debug', methods=['GET'])
def debug():
    """Debug route to check setup"""
    try:
        sample_programs = []
        sp_dir = os.path.join(BASE_DIR, 'sample_programs')
        if os.path.exists(sp_dir):
            sample_programs = os.listdir(sp_dir)
        
        static_files = []
        if os.path.exists(app.static_folder):
            static_files = os.listdir(app.static_folder)
        
        template_files = []
        if os.path.exists(app.template_folder):
            template_files = os.listdir(app.template_folder)
        
        return jsonify({
            'base_dir': BASE_DIR,
            'static_folder': app.static_folder,
            'template_folder': app.template_folder,
            'static_exists': os.path.exists(app.static_folder),
            'static_files': static_files,
            'templates_exist': os.path.exists(app.template_folder),
            'template_files': template_files,
            'sample_programs': sample_programs,
            'status': 'OK'
        })
    except Exception as e:
        print(f"[ERROR] Debug endpoint failed: {e}")
        return jsonify({'error': str(e)}), 500


@app.errorhandler(404)
def handle_404(e):
    """Handle 404 errors"""
    print(f"[ERROR] 404 Not Found: {request.path}")
    return jsonify({
        'error': 'Not Found',
        'path': request.path
    }), 404


@app.errorhandler(500)
def handle_500(e):
    """Handle 500 errors"""
    print(f"[ERROR] 500 Server Error: {e}")
    return jsonify({
        'error': 'Internal Server Error',
        'message': str(e)
    }), 500


if __name__ == '__main__':
    print('\n' + '='*70)
    print('🚀 EveCompiler IDE Startup')
    print('='*70)
    print(f'📂 Base Directory: {BASE_DIR}')
    print(f'📂 Static Folder: {app.static_folder}')
    print(f'   └─ Exists: {os.path.exists(app.static_folder)}')
    print(f'   └─ Files: {os.listdir(app.static_folder) if os.path.exists(app.static_folder) else "N/A"}')
    print(f'📂 Template Folder: {app.template_folder}')
    print(f'   └─ Exists: {os.path.exists(app.template_folder)}')
    print(f'   └─ Files: {os.listdir(app.template_folder) if os.path.exists(app.template_folder) else "N/A"}')
    print('='*70)
    print('🌐 Access the IDE at: http://localhost:5000')
    print('🔍 Debug info at: http://localhost:5000/debug')
    print('⏹️  Press Ctrl+C to stop')
    print('='*70 + '\n')
    
    app.run(debug=False, port=int(os.environ.get('PORT', 5000)), host='0.0.0.0', threaded=True)

