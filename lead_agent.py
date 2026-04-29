"""
AI Lead Agent System
Automatically scores, qualifies, and manages leads with Calendly integration
"""

import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sqlite3
import os

class LeadScorer:
    """AI-powered lead scoring system"""
    
    def __init__(self):
        self.scoring_criteria = {
            'company_size': {'large': 30, 'medium': 20, 'small': 10, 'startup': 5},
            'budget': {'high': 25, 'medium': 15, 'low': 5},
            'timeline': {'immediate': 20, 'soon': 15, 'later': 5},
            'industry_match': {'high': 15, 'medium': 10, 'low': 5},
            'engagement': {'high': 10, 'medium': 5, 'low': 0},
        }
    
    def calculate_score(self, lead_data: Dict) -> int:
        """Calculate lead score based on multiple factors"""
        score = 0
        
        # Company size
        company_size = lead_data.get('company_size', 'small').lower()
        score += self.scoring_criteria['company_size'].get(company_size, 5)
        
        # Budget
        budget = lead_data.get('budget', 'low').lower()
        score += self.scoring_criteria['budget'].get(budget, 5)
        
        # Timeline
        timeline = lead_data.get('timeline', 'later').lower()
        score += self.scoring_criteria['timeline'].get(timeline, 5)
        
        # Industry match
        industry_match = lead_data.get('industry_match', 'low').lower()
        score += self.scoring_criteria['industry_match'].get(industry_match, 5)
        
        # Engagement level
        engagement = lead_data.get('engagement', 'low').lower()
        score += self.scoring_criteria['engagement'].get(engagement, 0)
        
        return min(score, 100)  # Max score of 100
    
    def qualify_lead(self, score: int) -> str:
        """Determine lead qualification level"""
        if score >= 70:
            return 'hot'
        elif score >= 50:
            return 'warm'
        elif score >= 30:
            return 'cold'
        else:
            return 'disqualified'


class CalendlyIntegrator:
    """Calendly API integration for automatic booking"""
    
    def __init__(self, api_token: str):
        self.api_token = api_token
        self.base_url = "https://api.calendly.com"
        self.headers = {
            'Authorization': f'Bearer {api_token}',
            'Content-Type': 'application/json'
        }
    
    def get_event_types(self) -> List[Dict]:
        """Get available event types from Calendly"""
        response = requests.get(
            f"{self.base_url}/event_types",
            headers=self.headers
        )
        if response.status_code == 200:
            return response.json().get('collection', [])
        return []
    
    def create_booking_link(self, lead_email: str, lead_name: str, event_type_uri: str) -> Optional[Dict]:
        """Create a Calendly booking link for a lead"""
        booking_data = {
            "event_type_uuid": event_type_uri.split('/')[-1],
            "required_email": lead_email,
            "name": lead_name,
            "pre_fill": {
                "name": lead_name,
                "email": lead_email
            }
        }
        
        response = requests.post(
            f"{self.base_url}/scheduling_links",
            headers=self.headers,
            json=booking_data
        )
        
        if response.status_code == 201:
            return response.json()
        return None
    
    def schedule_event(self, lead_email: str, lead_name: str, event_type_uri: str, 
                     start_time: str) -> Optional[Dict]:
        """Schedule an event directly for a hot lead"""
        event_data = {
            "event_type_uuid": event_type_uri.split('/')[-1],
            "start_time": start_time,
            "email": lead_email,
            "name": lead_name,
            "status": "active"
        }
        
        response = requests.post(
            f"{self.base_url}/scheduled_events",
            headers=self.headers,
            json=event_data
        )
        
        if response.status_code == 201:
            return response.json()
        return None


class LeadManager:
    """Lead management system with database"""
    
    def __init__(self, db_path: str = "leads.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database for leads"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                company TEXT,
                company_size TEXT,
                budget TEXT,
                timeline TEXT,
                industry_match TEXT,
                engagement TEXT,
                score INTEGER,
                qualification TEXT,
                status TEXT DEFAULT 'new',
                calendly_link TEXT,
                scheduled_time TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_lead(self, lead_data: Dict) -> int:
        """Add a new lead to the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO leads (name, email, company, company_size, budget, timeline, 
                             industry_match, engagement, score, qualification, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            lead_data['name'],
            lead_data['email'],
            lead_data.get('company', ''),
            lead_data.get('company_size', 'small'),
            lead_data.get('budget', 'low'),
            lead_data.get('timeline', 'later'),
            lead_data.get('industry_match', 'low'),
            lead_data.get('engagement', 'low'),
            lead_data['score'],
            lead_data['qualification'],
            'new'
        ))
        
        lead_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return lead_id
    
    def update_lead_status(self, lead_id: int, status: str, notes: str = None):
        """Update lead status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if notes:
            cursor.execute('''
                UPDATE leads SET status = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (status, notes, lead_id))
        else:
            cursor.execute('''
                UPDATE leads SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (status, lead_id))
        
        conn.commit()
        conn.close()
    
    def update_calendly_booking(self, lead_id: int, calendly_link: str, scheduled_time: str = None):
        """Update lead with Calendly booking information"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if scheduled_time:
            cursor.execute('''
                UPDATE leads SET calendly_link = ?, scheduled_time = ?, 
                               status = 'booked', updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (calendly_link, scheduled_time, lead_id))
        else:
            cursor.execute('''
                UPDATE leads SET calendly_link = ?, status = 'link_sent', 
                               updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (calendly_link, lead_id))
        
        conn.commit()
        conn.close()
    
    def get_leads_by_status(self, status: str) -> List[Dict]:
        """Get leads by status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM leads WHERE status = ? ORDER BY created_at DESC
        ''', (status,))
        
        columns = [desc[0] for desc in cursor.description]
        leads = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return leads
    
    def get_all_leads(self) -> List[Dict]:
        """Get all leads"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM leads ORDER BY score DESC, created_at DESC')
        
        columns = [desc[0] for desc in cursor.description]
        leads = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return leads


class AILeadAgent:
    """Main AI Lead Agent that orchestrates the entire process"""
    
    def __init__(self, calendly_api_token: str = None):
        self.scorer = LeadScorer()
        self.manager = LeadManager()
        self.calendly = CalendlyIntegrator(calendly_api_token) if calendly_api_token else None
    
    def process_lead(self, lead_data: Dict) -> Dict:
        """Process a new lead through the entire pipeline"""
        # Calculate score
        score = self.scorer.calculate_score(lead_data)
        lead_data['score'] = score
        
        # Qualify lead
        qualification = self.scorer.qualify_lead(score)
        lead_data['qualification'] = qualification
        
        # Add to database
        lead_id = self.manager.add_lead(lead_data)
        
        result = {
            'lead_id': lead_id,
            'score': score,
            'qualification': qualification,
            'action_taken': None
        }
        
        # Take action based on qualification
        if qualification == 'hot' and self.calendly:
            # Book directly on Calendly
            event_types = self.calendly.get_event_types()
            if event_types:
                event_type_uri = event_types[0].get('uri')
                # Schedule for next available slot
                start_time = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%dT09:00:00Z')
                booking = self.calendly.schedule_event(
                    lead_data['email'],
                    lead_data['name'],
                    event_type_uri,
                    start_time
                )
                if booking:
                    self.manager.update_calendly_booking(
                        lead_id,
                        booking.get('booking_url'),
                        start_time
                    )
                    result['action_taken'] = 'scheduled_on_calendly'
                else:
                    # Fallback to booking link
                    link = self.calendly.create_booking_link(
                        lead_data['email'],
                        lead_data['name'],
                        event_type_uri
                    )
                    if link:
                        self.manager.update_calendly_booking(lead_id, link.get('scheduling_url'))
                        result['action_taken'] = 'calendly_link_sent'
        
        elif qualification == 'warm':
            # Send nurturing email with Calendly link
            if self.calendly:
                event_types = self.calendly.get_event_types()
                if event_types:
                    link = self.calendly.create_booking_link(
                        lead_data['email'],
                        lead_data['name'],
                        event_types[0].get('uri')
                    )
                    if link:
                        self.manager.update_calendly_booking(lead_id, link.get('scheduling_url'))
                        result['action_taken'] = 'nurturing_with_calendly'
            self.manager.update_lead_status(lead_id, 'nurturing', 'Warm lead - nurturing sequence started')
        
        elif qualification == 'cold':
            # Add to cold outreach sequence
            self.manager.update_lead_status(lead_id, 'cold_outreach', 'Cold lead - added to outreach sequence')
            result['action_taken'] = 'added_to_cold_outreach'
        
        else:  # disqualified
            self.manager.update_lead_status(lead_id, 'disqualified', 'Lead disqualified - low score')
            result['action_taken'] = 'disqualified'
        
        return result
    
    def process_batch_leads(self, leads: List[Dict]) -> List[Dict]:
        """Process multiple leads in batch"""
        results = []
        for lead in leads:
            result = self.process_lead(lead)
            results.append(result)
        return results
    
    def get_dashboard_data(self) -> Dict:
        """Get dashboard statistics"""
        all_leads = self.manager.get_all_leads()
        
        stats = {
            'total_leads': len(all_leads),
            'hot_leads': len([l for l in all_leads if l['qualification'] == 'hot']),
            'warm_leads': len([l for l in all_leads if l['qualification'] == 'warm']),
            'cold_leads': len([l for l in all_leads if l['qualification'] == 'cold']),
            'disqualified': len([l for l in all_leads if l['qualification'] == 'disqualified']),
            'booked': len([l for l in all_leads if l['status'] == 'booked']),
            'average_score': sum(l['score'] for l in all_leads) / len(all_leads) if all_leads else 0,
            'recent_leads': all_leads[:10]
        }
        
        return stats


# Example usage
if __name__ == "__main__":
    # Initialize agent with your Calendly API token
    CALENDLY_TOKEN = "eyJraWQiOiIxY2UxZTEzNjE3ZGNmNzY2YjNjZWJjY2Y4ZGM1YmFmYThhNjVlNjg0MDIzZjdjMzJiZTgzNDliMjM4MDEzNWI0IiwidHlwIjoiUEFUIiwiYWxnIjoiRVMyNTYifQ.eyJpc3MiOiJodHRwczovL2F1dGguY2FsZW5kbHkuY29tIiwiaWF0IjoxNzc3NDc4NDE0LCJqdGkiOiIyNzQyNzQwNy1mNmYwLTRmNzItOWFkMi01ZmFlZTI4ZDVlN2UiLCJ1c2VyX3V1aWQiOiI0Nzk4ZDM5Ny03ZWIzLTRjMzItYjA3MC01YjcyMjYzODk4MDkiLCJzY29wZSI6IndlYmhvb2tzOnJlYWQgd2ViaG9va3M6d3JpdGUifQ.Sj76YHJCCAgijCbCjmiZKqzK-UhK5ApmN8Yfmi3xLNtuMX5MRP1zx1Dpdui9Cz35CCNxR-qF5YsS_6NxKjrpJg"
    agent = AILeadAgent(calendly_api_token=CALENDLY_TOKEN)
    
    # Example lead data
    example_lead = {
        'name': 'John Doe',
        'email': 'john@example.com',
        'company': 'Tech Corp',
        'company_size': 'large',
        'budget': 'high',
        'timeline': 'immediate',
        'industry_match': 'high',
        'engagement': 'high'
    }
    
    # Process lead
    result = agent.process_lead(example_lead)
    print(f"Lead processed: {result}")
    
    # Get dashboard data
    dashboard = agent.get_dashboard_data()
    print(f"Dashboard stats: {dashboard}")
