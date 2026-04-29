"""
Flask Web Application for AI Lead Agent
Fully automated lead management system with web interface
"""

import os
from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS
from lead_agent import AILeadAgent
import threading
import time
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Initialize agent with Calendly token from environment variable
CALENDLY_TOKEN = os.getenv('CALENDLY_API_TOKEN')
if not CALENDLY_TOKEN:
    print("⚠️  WARNING: CALENDLY_API_TOKEN environment variable not set")
    print("   Set it in PythonAnywhere Web tab → Environment variables")
    # For local development, you can uncomment the line below:
    # CALENDLY_TOKEN = "your_token_here"

agent = AILeadAgent(calendly_api_token=CALENDLY_TOKEN)

# Read dashboard HTML
with open('dashboard_app.html', 'r', encoding='utf-8') as f:
    dashboard_html = f.read()

# API Routes
@app.route('/')
def home():
    """Serve the dashboard"""
    return render_template_string(dashboard_html)

@app.route('/api/leads', methods=['GET'])
def get_leads():
    """Get all leads"""
    try:
        leads = agent.manager.get_all_leads()
        return jsonify(leads)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/leads', methods=['POST'])
def add_lead():
    """Add a new lead"""
    try:
        lead_data = request.json
        result = agent.process_lead(lead_data)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard', methods=['GET'])
def dashboard():
    """Get dashboard statistics"""
    try:
        stats = agent.get_dashboard_data()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/leads/<int:lead_id>', methods=['GET'])
def get_lead(lead_id):
    """Get a specific lead"""
    try:
        leads = agent.manager.get_all_leads()
        lead = next((l for l in leads if l['id'] == lead_id), None)
        if lead:
            return jsonify(lead)
        return jsonify({'error': 'Lead not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/leads/<int:lead_id>/status', methods=['PUT'])
def update_lead_status(lead_id):
    """Update lead status"""
    try:
        data = request.json
        status = data.get('status')
        notes = data.get('notes')
        agent.manager.update_lead_status(lead_id, status, notes)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports', methods=['GET'])
def get_reports():
    """Get detailed reports"""
    try:
        leads = agent.manager.get_all_leads()
        
        # Calculate detailed statistics
        total = len(leads)
        hot = len([l for l in leads if l['qualification'] == 'hot'])
        warm = len([l for l in leads if l['qualification'] == 'warm'])
        cold = len([l for l in leads if l['qualification'] == 'cold'])
        disqualified = len([l for l in leads if l['qualification'] == 'disqualified'])
        
        booked = len([l for l in leads if l['status'] == 'booked'])
        nurturing = len([l for l in leads if l['status'] == 'nurturing'])
        cold_outreach = len([l for l in leads if l['status'] == 'cold_outreach'])
        
        avg_score = sum(l['score'] for l in leads) / total if total else 0
        
        # Recent activity
        recent_leads = leads[:10]
        
        # Conversion rates
        hot_to_booked = (booked / hot * 100) if hot > 0 else 0
        
        report = {
            'summary': {
                'total_leads': total,
                'hot_leads': hot,
                'warm_leads': warm,
                'cold_leads': cold,
                'disqualified': disqualified,
                'booked': booked,
                'conversion_rate': round(hot_to_booked, 2),
                'average_score': round(avg_score, 2)
            },
            'status_breakdown': {
                'booked': booked,
                'nurturing': nurturing,
                'cold_outreach': cold_outreach,
                'disqualified': disqualified
            },
            'recent_activity': recent_leads,
            'qualification_distribution': {
                'hot': hot,
                'warm': warm,
                'cold': cold,
                'disqualified': disqualified
            },
            'generated_at': datetime.now().isoformat()
        }
        
        return jsonify(report)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'calendly_connected': bool(CALENDLY_TOKEN)
    })

# Background task for automated processing (optional)
def background_processor():
    """Background task to process leads automatically"""
    while True:
        try:
            # Check for new leads that need processing
            leads = agent.manager.get_leads_by_status('new')
            for lead in leads:
                # Re-process the lead
                lead_data = {
                    'name': lead['name'],
                    'email': lead['email'],
                    'company': lead['company'],
                    'company_size': lead['company_size'],
                    'budget': lead['budget'],
                    'timeline': lead['timeline'],
                    'industry_match': lead['industry_match'],
                    'engagement': lead['engagement']
                }
                agent.process_lead(lead_data)
            
            # Sleep for 5 minutes before next check
            time.sleep(300)
        except Exception as e:
            print(f"Background processor error: {e}")
            time.sleep(60)

# Start background processor
def start_background_processor():
    """Start the background processor thread"""
    processor_thread = threading.Thread(target=background_processor, daemon=True)
    processor_thread.start()

if __name__ == '__main__':
    # Get port from environment variable (Railway sets this)
    port = int(os.getenv('PORT', 5000))
    
    print("🚀 Starting AI Lead Agent Web Application...")
    print(f"📊 Dashboard will be available at: http://localhost:{port}")
    print("🔗 API Endpoints:")
    print("   - GET  /api/leads - Get all leads")
    print("   - POST /api/leads - Add new lead")
    print("   - GET  /api/dashboard - Get dashboard stats")
    print("   - GET  /api/reports - Get detailed reports")
    print("   - GET  /api/health - Health check")
    
    # Start background processor
    start_background_processor()
    
    # Run Flask app
    # Use debug=False for production
    app.run(debug=False, host='0.0.0.0', port=port)
