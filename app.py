#!/usr/bin/env python3

import os
import sys
import json
import threading
import time
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, jsonify, request, send_file
from flask_socketio import SocketIO, emit
import logging

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from engagement_analyzer import EngagementAnalyzer

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', os.urandom(24).hex())
socketio = SocketIO(app, cors_allowed_origins="*")

# Global variables
analyzer = None
current_analysis = None
analysis_in_progress = False

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/webapp.log', mode='a')
        ]
    )

def initialize_analyzer():
    global analyzer
    try:
        analyzer = EngagementAnalyzer()
        app.logger.info("Engagement analyzer initialized successfully")
        return True
    except Exception as e:
        app.logger.error(f"Failed to initialize analyzer: {e}")
        return False

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/status')
def get_status():
    global analyzer, analysis_in_progress
    
    if analyzer is None:
        return jsonify({
            'status': 'error',
            'message': 'Analyzer not initialized',
            'analyzer_ready': False,
            'analysis_in_progress': False
        })
    
    # Test Slack connection
    try:
        slack_connected = analyzer.test_slack_connection()
    except:
        slack_connected = False
    
    # Get database stats
    try:
        db_stats = analyzer.get_database_stats()
    except:
        db_stats = {}
    
    return jsonify({
        'status': 'ready',
        'analyzer_ready': True,
        'slack_connected': slack_connected,
        'analysis_in_progress': analysis_in_progress,
        'database_stats': db_stats,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/analyze', methods=['POST'])
def start_analysis():
    global analysis_in_progress, current_analysis
    
    if analysis_in_progress:
        return jsonify({
            'status': 'error',
            'message': 'Analysis already in progress'
        }), 400
    
    if analyzer is None:
        return jsonify({
            'status': 'error',
            'message': 'Analyzer not initialized'
        }), 500
    
    # Get parameters
    data = request.get_json() or {}
    days_back = data.get('days', 7)
    
    # Start analysis in background thread
    analysis_in_progress = True
    thread = threading.Thread(target=run_analysis_background, args=(days_back,))
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'status': 'started',
        'message': f'Analysis started for {days_back} days',
        'analysis_id': str(int(time.time()))
    })

def run_analysis_background(days_back):
    global analysis_in_progress, current_analysis
    
    try:
        # Send progress updates
        socketio.emit('analysis_progress', {
            'stage': 'starting',
            'message': 'Starting analysis...',
            'progress': 0
        })
        
        # Test connection
        socketio.emit('analysis_progress', {
            'stage': 'connection',
            'message': 'Testing Slack connection...',
            'progress': 10
        })
        
        if not analyzer.test_slack_connection():
            raise Exception("Failed to connect to Slack API")
        
        # Run analysis
        socketio.emit('analysis_progress', {
            'stage': 'collecting',
            'message': f'Collecting {days_back} days of data...',
            'progress': 20
        })
        
        result = analyzer.run_analysis(
            days_back=days_back,
            generate_reports=True,
            print_summary=False,
            cleanup=True
        )
        
        socketio.emit('analysis_progress', {
            'stage': 'analyzing',
            'message': 'Analyzing sentiment with GPT...',
            'progress': 60
        })
        
        time.sleep(1)  # Let GPT analysis complete
        
        socketio.emit('analysis_progress', {
            'stage': 'reporting',
            'message': 'Generating reports...',
            'progress': 80
        })
        
        # Store result
        activity_patterns = result.get('activity_patterns', {})
        engagement_metrics = result.get('engagement_metrics', {})
        burnout_alerts = result.get('burnout_alerts', {})
        
        # Calculate additional metrics
        total_reactions = sum(
            channel_data.get('total_reactions', 0) 
            for channel_data in engagement_metrics.get('by_channel', {}).values()
        )
        
        # Calculate average thread participation
        thread_participation = 0
        channel_count = len(engagement_metrics.get('by_channel', {}))
        if channel_count > 0:
            thread_participation = sum(
                channel_data.get('total_messages', 0) * 0.1  # Estimate based on engagement
                for channel_data in engagement_metrics.get('by_channel', {}).values()
            ) / channel_count
        
        # Determine overall risk level
        risk_level = 'LOW'
        if burnout_alerts:
            high_risk_count = sum(1 for alert in burnout_alerts.values() if alert.get('risk_level') == 'high')
            medium_risk_count = sum(1 for alert in burnout_alerts.values() if alert.get('risk_level') == 'medium')
            
            if high_risk_count > 0:
                risk_level = 'HIGH'
            elif medium_risk_count > 0:
                risk_level = 'MEDIUM'
        
        current_analysis = {
            'timestamp': datetime.now().isoformat(),
            'days_analyzed': days_back,
            'results': {
                'total_messages': result.get('analysis_metadata', {}).get('total_messages', 0),
                'overall_sentiment': result.get('engagement_summary', {}).get('overall_avg_sentiment', 0),
                'overall_engagement': result.get('engagement_summary', {}).get('overall_avg_engagement', 0),
                'channels_analyzed': result.get('analysis_metadata', {}).get('channels_analyzed', []),
                'burnout_alerts': len(result.get('burnout_alerts', {})),
                'sentiment_distribution': result.get('engagement_summary', {}).get('sentiment_distribution', {}),
                'report_paths': result.get('report_paths', []),
                # Additional metrics for enhanced dashboard
                'total_reactions': total_reactions,
                'thread_participation': thread_participation,
                'peak_hour': activity_patterns.get('peak_hour', 'N/A'),
                'peak_day': activity_patterns.get('peak_day', 'N/A'),
                'risk_level': risk_level,
                'recommendations': result.get('recommendations', []),
                'weekly_patterns': result.get('sentiment_analysis', {}).get('weekly_patterns', {}),
                'channel_breakdown': engagement_metrics.get('by_channel', {}),
                'burnout_details': burnout_alerts
            },
            'raw_data': result
        }
        
        socketio.emit('analysis_progress', {
            'stage': 'complete',
            'message': 'Analysis completed successfully!',
            'progress': 100,
            'results': current_analysis['results']
        })
        
    except Exception as e:
        app.logger.error(f"Analysis failed: {e}")
        socketio.emit('analysis_progress', {
            'stage': 'error',
            'message': f'Analysis failed: {str(e)}',
            'progress': 0
        })
    
    finally:
        analysis_in_progress = False

@app.route('/api/results')
def get_results():
    global current_analysis
    
    if current_analysis is None:
        return jsonify({
            'status': 'no_data',
            'message': 'No analysis results available'
        })
    
    return jsonify({
        'status': 'success',
        'data': current_analysis
    })

@app.route('/api/reports')
def list_reports():
    reports_dir = Path('reports')
    if not reports_dir.exists():
        return jsonify({'reports': []})
    
    reports = []
    for file_path in reports_dir.glob('engagement_*'):
        if file_path.is_file():
            reports.append({
                'filename': file_path.name,
                'path': str(file_path),
                'size': file_path.stat().st_size,
                'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                'type': 'HTML' if file_path.suffix == '.html' else 'JSON'
            })
    
    # Sort by modification time, newest first
    reports.sort(key=lambda x: x['modified'], reverse=True)
    
    return jsonify({'reports': reports})

@app.route('/api/reports/<filename>')
def download_report(filename):
    reports_dir = Path('reports')
    file_path = reports_dir / filename
    
    if not file_path.exists() or not file_path.is_file():
        return jsonify({'error': 'Report not found'}), 404
    
    return send_file(file_path, as_attachment=True)

@app.route('/api/reports/<filename>/view')
def view_report(filename):
    reports_dir = Path('reports')
    file_path = reports_dir / filename
    
    if not file_path.exists() or not file_path.is_file():
        return jsonify({'error': 'Report not found'}), 404
    
    if filename.endswith('.html'):
        return send_file(file_path)
    elif filename.endswith('.json'):
        with open(file_path, 'r') as f:
            data = json.load(f)
        return jsonify(data)
    else:
        return jsonify({'error': 'Unsupported file type'}), 400

@socketio.on('connect')
def handle_connect():
    emit('connected', {'message': 'Connected to Engagement Pulse'})
    app.logger.info('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    app.logger.info('Client disconnected')

if __name__ == '__main__':
    # Ensure directories exist
    os.makedirs('logs', exist_ok=True)
    os.makedirs('reports', exist_ok=True)
    
    # Setup logging
    setup_logging()
    
    # Initialize analyzer
    app.logger.info("Initializing Engagement Analyzer...")
    if initialize_analyzer():
        app.logger.info("✅ Ready to serve!")
        # Run the app
        socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
    else:
        app.logger.error("❌ Failed to initialize. Check your configuration.")
        sys.exit(1)