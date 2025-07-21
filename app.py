from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file
import requests
from bs4 import BeautifulSoup
import json
import os
import sqlite3
from datetime import datetime, timedelta
import schedule
import time
import threading
from urllib.parse import urljoin, urlparse
import re
import subprocess
import hashlib
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import io
import tempfile

app = Flask(__name__)

# Database setup with migration
def init_db():
    """Initialize SQLite database with migration support"""
    conn = sqlite3.connect('competitor_tracker.db')
    cursor = conn.cursor()
    
    # Check if tables exist and get their structure
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    existing_tables = [row[0] for row in cursor.fetchall()]
    
    # Competitors table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS competitors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            website TEXT NOT NULL,
            changelog_url TEXT,
            added_at TEXT,
            last_checked TEXT,
            status TEXT DEFAULT 'active'
        )
    ''')
    
    # Changes table - check if it needs migration
    if 'changes' in existing_tables:
        # Check current schema
        cursor.execute("PRAGMA table_info(changes)")
        columns = [row[1] for row in cursor.fetchall()]
        
        # Add missing columns if they don't exist
        if 'news_title' not in columns:
            cursor.execute('ALTER TABLE changes ADD COLUMN news_title TEXT')
        if 'news_excerpt' not in columns:
            cursor.execute('ALTER TABLE changes ADD COLUMN news_excerpt TEXT')
        if 'source_links' not in columns:
            cursor.execute('ALTER TABLE changes ADD COLUMN source_links TEXT')
    else:
        # Create new table with all columns
        cursor.execute('''
            CREATE TABLE changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                competitor_id INTEGER,
                competitor_name TEXT,
                content TEXT,
                content_hash TEXT,
                changelog_content TEXT,
                analysis TEXT,
                ai_summary TEXT,
                detected_at TEXT,
                url TEXT,
                change_type TEXT,
                importance_score INTEGER DEFAULT 5,
                news_title TEXT,
                news_excerpt TEXT,
                source_links TEXT,
                FOREIGN KEY (competitor_id) REFERENCES competitors (id)
            )
        ''')
    
    # Settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    # Content snapshots for comparison
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS content_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            competitor_id INTEGER,
            content_hash TEXT,
            full_content TEXT,
            scraped_at TEXT,
            FOREIGN KEY (competitor_id) REFERENCES competitors (id)
        )
    ''')
    
    # Company profile table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS company_profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            website TEXT,
            description TEXT,
            industry TEXT,
            founded_year INTEGER,
            size TEXT,
            headquarters TEXT,
            key_products TEXT,
            target_market TEXT,
            competitive_advantages TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    
    # Company news/updates table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS company_updates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT,
            update_type TEXT,
            importance_score INTEGER DEFAULT 5,
            date_published TEXT,
            source_url TEXT,
            tags TEXT,
            created_at TEXT
        )
    ''')
    
    # Competitive insights table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS competitive_insights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            competitor_id INTEGER,
            insight_type TEXT,
            insight_content TEXT,
            impact_level TEXT,
            recommendation TEXT,
            created_at TEXT,
            FOREIGN KEY (competitor_id) REFERENCES competitors (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database initialized and migrated successfully")

# Initialize database on startup
init_db()

class PDFGenerator:
    """Enhanced PDF generation for competitor analysis reports"""
    
    def __init__(self):
        try:
            self.styles = getSampleStyleSheet()
            self.setup_custom_styles()
        except ImportError:
            print("⚠️ ReportLab not installed. PDF generation disabled.")
            self.styles = None
    
    def setup_custom_styles(self):
        """Setup custom PDF styles"""
        if not self.styles:
            return
        
        # Title style
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#2D3748')
        )
        
        # Subtitle style
        self.subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=20,
            textColor=colors.HexColor('#4A5568')
        )
        
        # Body style
        self.body_style = ParagraphStyle(
            'CustomBody',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=12,
            alignment=TA_JUSTIFY,
            textColor=colors.HexColor('#2D3748')
        )
    
    def generate_comprehensive_report(self, changes_data, summary_text):
        """Generate comprehensive PDF report with all changes and analysis"""
        if not self.styles:
            return None
        
        try:
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
            
            # Container for the 'Flowable' objects
            elements = []
            
            # Title
            title = Paragraph("🤖 AI-Powered Competitor Intelligence Report", self.title_style)
            elements.append(title)
            elements.append(Spacer(1, 20))
            
            # Report metadata
            report_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")
            metadata = Paragraph(f"<b>Generated:</b> {report_date}<br/><b>Total Changes Analyzed:</b> {len(changes_data)}", self.body_style)
            elements.append(metadata)
            elements.append(Spacer(1, 30))
            
            # Executive Summary
            if summary_text:
                elements.append(Paragraph("📊 Executive Summary", self.subtitle_style))
                formatted_summary = self.format_ai_summary(summary_text)
                elements.append(Paragraph(formatted_summary, self.body_style))
                elements.append(Spacer(1, 20))
            
            # Detailed Changes
            for change in changes_data[:20]:  # Limit to 20 changes for PDF
                elements.extend(self.format_change_entry(change))
            
            # Build PDF
            doc.build(elements)
            buffer.seek(0)
            return buffer
        except Exception as e:
            print(f"PDF generation error: {e}")
            return None
    
    def format_ai_summary(self, summary_text):
        """Format AI summary for PDF"""
        lines = summary_text.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if line:
                if line.endswith(':') or line.startswith('##'):
                    formatted_lines.append(f"<b>{line}</b>")
                elif line.startswith('•') or line.startswith('-'):
                    formatted_lines.append(f"&nbsp;&nbsp;&nbsp;&nbsp;{line}")
                else:
                    formatted_lines.append(line)
        
        return '<br/>'.join(formatted_lines)
    
    def format_change_entry(self, change):
        """Format individual change entry"""
        elements = []
        
        competitor_name = change.get('competitor_name', 'Unknown')
        change_date = change.get('detected_at', '')[:10] if change.get('detected_at') else 'Unknown'
        importance = change.get('importance_score', 5)
        
        header_text = f"<b>{competitor_name}</b> | {change_date} | Score: {importance}/10"
        header = Paragraph(header_text, self.body_style)
        elements.append(header)
        
        analysis = change.get('analysis', 'No analysis available')
        analysis_para = Paragraph(f"<b>Analysis:</b> {analysis}", self.body_style)
        elements.append(analysis_para)
        
        elements.append(Spacer(1, 15))
        return elements

class OllamaAI:
    """Enhanced AI analysis using Ollama"""
    
    def __init__(self):
        self.model = "llama3"
    
    def analyze_content_changes(self, old_content, new_content, competitor_name, website):
        """Use Ollama to analyze content changes with news focus"""
        if not old_content or not new_content:
            return {
                'analysis': f"Started monitoring {competitor_name} - baseline established for future news detection",
                'change_type': "first_scan",
                'importance_score': 3,
                'news_title': f"{competitor_name} Added to Monitoring",
                'news_excerpt': f"Now tracking {competitor_name} for product updates, announcements, and market moves",
                'source_links': website
            }
        
        # Create news-focused analysis prompt for Ollama
        prompt = f"""You are a business news analyst monitoring competitor {competitor_name} for market intelligence.

WEBSITE: {website}

PREVIOUS CONTENT (first 800 chars):
{old_content[:800]}

NEW CONTENT (first 800 chars):
{new_content[:800]}

Analyze these changes as a business news story. Provide:

CHANGE_TYPE: [product_launch/feature_update/pricing_change/partnership/acquisition/content_update/press_release/blog_post]
IMPORTANCE: [1-10 where 8-10=breaking news, 6-7=important updates, 4-5=routine news, 1-3=minor changes]
NEWS_TITLE: [Write as a business news headline, max 70 chars]
NEWS_EXCERPT: [Write as a news summary focusing on business impact, max 180 chars]
ANALYSIS: [Business intelligence analysis focusing on competitive implications, max 250 chars]

Focus on business impact, market implications, and competitive intelligence rather than technical details."""
        
        try:
            result = self._call_ollama(prompt)
            return self._parse_enhanced_response(result, website)
        except Exception as e:
            print(f"⚠️ Ollama analysis failed: {e}")
            return self._fallback_news_analysis(old_content, new_content, competitor_name, website)
    
    def generate_competitive_insights(self, company_data, competitor_changes, timeframe_days=30):
        """Generate competitive insights comparing company with competitors"""
        
        # First, get industry-specific market data
        industry_context = self._get_industry_context(company_data.get('industry', 'Technology'))
        
        prompt = f"""You are a competitive intelligence analyst. Analyze the competitive landscape and provide strategic insights.

COMPANY PROFILE:
Name: {company_data.get('name', 'Our Company')}
Industry: {company_data.get('industry', 'Technology')}
Key Products: {company_data.get('key_products', 'Various products')}
Target Market: {company_data.get('target_market', 'General market')}
Competitive Advantages: {company_data.get('competitive_advantages', 'Innovation and quality')}

INDUSTRY CONTEXT:
{industry_context}

COMPETITOR ACTIVITY (Last {timeframe_days} days):
{self._format_competitor_activity(competitor_changes)}

Provide analysis in this format:

## 🎯 COMPETITIVE POSITIONING
[How our company stands against recent competitor moves and industry trends]

## 🚨 THREATS & OPPORTUNITIES  
[Key threats to watch and opportunities to capitalize on based on industry analysis]

## 💡 STRATEGIC RECOMMENDATIONS
[Specific actionable recommendations based on competitor activity and industry trends]

## 📊 MARKET TRENDS
[Emerging trends from competitor analysis and industry research]

## ⚡ IMMEDIATE ACTIONS
[What to do in the next 30 days based on competitive intelligence]

## 🔍 INDUSTRY-SPECIFIC INSIGHTS
[Insights specific to the {company_data.get('industry', 'Technology')} industry]

Keep analysis strategic, actionable, and focused on business impact with industry-specific context."""
        
        try:
            return self._call_ollama(prompt)
        except Exception as e:
            print(f"⚠️ Competitive insights generation failed: {e}")
            return self._fallback_competitive_insights_with_industry(competitor_changes, company_data.get('industry', 'Technology'))
    
    def _get_industry_context(self, industry):
        """Get industry-specific context and trends"""
        industry_contexts = {
            'Technology': """
            Current Tech Industry Trends:
            • AI/ML adoption accelerating across all sectors
            • Cloud-first strategies becoming standard
            • Cybersecurity concerns driving investment
            • Remote work tools and collaboration platforms in high demand
            • API-first and microservices architecture trending
            • Sustainability and green tech initiatives growing
            • Data privacy regulations impacting product development
            """,
            'Healthcare': """
            Current Healthcare Industry Trends:
            • Telemedicine and digital health solutions expanding
            • AI-powered diagnostics and treatment planning
            • Patient data security and HIPAA compliance critical
            • Personalized medicine and genomics advancing
            • Healthcare automation and workflow optimization
            • Mental health and wellness focus increasing
            • Regulatory compliance and FDA approvals key factors
            """,
            'Finance': """
            Current Finance Industry Trends:
            • Digital banking and fintech disruption continuing
            • Cryptocurrency and blockchain adoption growing
            • Regulatory compliance and risk management critical
            • AI-powered fraud detection and risk assessment
            • Open banking and API integration expanding
            • ESG investing and sustainable finance trending
            • Real-time payments and instant settlement demand
            """,
            'E-commerce': """
            Current E-commerce Industry Trends:
            • Omnichannel customer experience essential
            • AI-powered personalization and recommendations
            • Social commerce and influencer marketing growing
            • Sustainability and ethical sourcing important
            • Mobile-first shopping experiences critical
            • Same-day and instant delivery expectations
            • AR/VR for virtual shopping experiences emerging
            """,
            'SaaS': """
            Current SaaS Industry Trends:
            • Product-led growth strategies dominating
            • AI and automation integration essential
            • Customer success and retention focus critical
            • API-first and integration capabilities key
            • Security and compliance requirements increasing
            • Usage-based pricing models trending
            • Vertical SaaS solutions gaining traction
            """
        }
        
        return industry_contexts.get(industry, f"""
        General {industry} Industry Context:
        • Digital transformation accelerating across the sector
        • Customer experience and satisfaction becoming key differentiators
        • Data-driven decision making and analytics adoption growing
        • Sustainability and social responsibility increasingly important
        • Regulatory compliance and risk management critical
        • Innovation and agility essential for competitive advantage
        • Partnership and ecosystem strategies becoming more common
        """)
    
    def _fallback_competitive_insights_with_industry(self, changes, industry):
        """Enhanced fallback competitive insights with industry context"""
        high_impact_changes = [c for c in changes if c.get('importance_score', 5) >= 7]
        
        industry_specific_advice = {
            'Technology': "Focus on AI integration, cloud scalability, and developer experience",
            'Healthcare': "Prioritize patient outcomes, regulatory compliance, and data security",
            'Finance': "Emphasize security, regulatory compliance, and customer trust",
            'E-commerce': "Optimize for mobile experience, personalization, and logistics",
            'SaaS': "Focus on product-led growth, customer success, and integration capabilities"
        }
        
        advice = industry_specific_advice.get(industry, "Focus on innovation, customer experience, and market differentiation")
        
        insights = f"""## 🎯 COMPETITIVE POSITIONING
Based on recent competitor activity, we've detected {len(changes)} total updates with {len(high_impact_changes)} high-impact changes in the {industry} sector.

## 🚨 THREATS & OPPORTUNITIES
• {len(high_impact_changes)} high-priority competitor moves require attention
• Market activity suggests increased competition in the {industry} space
• Opportunity to differentiate while competitors focus on incremental updates

## 💡 STRATEGIC RECOMMENDATIONS
• Monitor competitor pricing and feature announcements closely
• Accelerate product roadmap to stay competitive in {industry}
• Consider strategic partnerships to counter competitor moves
• {advice}

## 📊 MARKET TRENDS
• Increased competitor activity indicates growing {industry} market interest
• Focus on innovation and customer experience as differentiators
• Industry-specific compliance and standards becoming more important

## ⚡ IMMEDIATE ACTIONS
• Review product positioning against recent competitor launches
• Update competitive analysis documentation for {industry} trends
• Brief sales team on competitor changes and industry developments

## 🔍 INDUSTRY-SPECIFIC INSIGHTS
• {industry} sector showing signs of consolidation and increased competition
• Key success factors include innovation, customer satisfaction, and operational efficiency
• Regulatory and compliance considerations becoming more critical"""
        
        return insights
    
    def _format_competitor_activity(self, changes):
        """Format competitor changes for AI analysis"""
        activity_text = ""
        for change in changes[:10]:  # Limit to 10 most recent
            activity_text += f"""
• {change['competitor_name']} - {change['detected_at'][:10]}
  Type: {change.get('change_type', 'update').replace('_', ' ').title()}
  Impact: {change.get('importance_score', 5)}/10
  News: {change.get('news_title', 'Update detected')}
  Analysis: {change.get('analysis', 'No analysis')[:100]}...
"""
        return activity_text
    
    def _fallback_news_analysis(self, old_content, new_content, competitor_name, website):
        """Fallback news-focused analysis when Ollama fails"""
        old_words = set(old_content.lower().split())
        new_words = set(new_content.lower().split())
        
        added_words = new_words - old_words
        removed_words = old_words - new_words
        
        # Look for business-relevant keywords
        business_keywords = {
            'launch', 'release', 'announce', 'partnership', 'acquisition', 'merger',
            'funding', 'investment', 'expansion', 'new', 'update', 'feature',
            'product', 'service', 'pricing', 'price', 'customer', 'market'
        }
        
        relevant_additions = added_words.intersection(business_keywords)
        
        if len(added_words) > 50 or len(removed_words) > 50 or relevant_additions:
            return {
                'change_type': "major_announcement" if relevant_additions else "major_update",
                'importance_score': 8 if relevant_additions else 7,
                'analysis': f"{competitor_name} made significant website updates, potentially indicating new business developments or product announcements",
                'news_title': f"{competitor_name} Major Business Update Detected",
                'news_excerpt': f"Significant changes detected on {competitor_name}'s website suggesting new announcements or product developments",
                'source_links': website
            }
        elif len(added_words) > 10 or len(removed_words) > 10:
            return {
                'change_type': "content_update",
                'importance_score': 5,
                'analysis': f"{competitor_name} updated their website content, possibly with new information about products or services",
                'news_title': f"{competitor_name} Website Content Updated",
                'news_excerpt': f"Moderate content changes detected on {competitor_name}'s website with potential business relevance",
                'source_links': website
            }
        else:
            return {
                'change_type': "minor_update",
                'importance_score': 3,
                'analysis': f"{competitor_name} made minor website adjustments, likely routine maintenance or small content updates",
                'news_title': f"{competitor_name} Minor Website Updates",
                'news_excerpt': f"Small routine updates detected on {competitor_name}'s website",
                'source_links': website
            }
    
    def generate_weekly_summary(self, changes_data):
        """Generate intelligent weekly summary focusing on news and updates"""
        if not changes_data:
            return "No significant competitor news or updates detected this week."
        
        # Prepare news-focused data for analysis
        news_items = []
        high_priority_news = []
        competitors_with_updates = set()
        
        for change in changes_data[:15]:  # Limit to 15 most recent changes
            competitors_with_updates.add(change['competitor_name'])
            
            news_item = {
                'competitor': change['competitor_name'],
                'title': change.get('news_title', f"{change['competitor_name']} Update"),
                'excerpt': change.get('news_excerpt', change['analysis'][:100]),
                'importance': change.get('importance_score', 5),
                'type': change.get('change_type', 'update').replace('_', ' ').title(),
                'date': change['detected_at'][:10]
            }
            
            news_items.append(news_item)
            
            if change.get('importance_score', 5) >= 7:
                high_priority_news.append(news_item)
        
        # Create news-focused prompt for Ollama
        news_text = ""
        for item in news_items:
            news_text += f"""📰 {item['competitor']} - {item['date']}
Headline: {item['title']}
Summary: {item['excerpt']}
Priority: {item['importance']}/10 | Type: {item['type']}
---
"""
        
        prompt = f"""You are a business news analyst creating a weekly competitive intelligence newsletter.

COMPETITOR NEWS & UPDATES THIS WEEK:
{news_text}

OVERVIEW:
- Total News Items: {len(news_items)}
- High Priority Updates: {len(high_priority_news)}
- Active Competitors: {len(competitors_with_updates)}

Create a professional newsletter-style summary that includes:

## 📰 Weekly Competitor News Digest

### 🔥 Top Stories This Week
[Highlight the most important news items as headlines with brief descriptions]

### 📊 Market Intelligence Summary
[Overall assessment of competitive landscape movements]

### 🚨 Priority Alerts
[Critical updates that require immediate attention]

### 📈 Competitor Activity Breakdown
[Brief overview of which competitors were most active]

### 💡 Strategic Insights
[Key takeaways and implications for our business]

Write this as a news digest focusing on business updates, product launches, market moves, and strategic announcements. Keep it professional and actionable, under 400 words."""
        
        try:
            return self._call_ollama(prompt)
        except Exception as e:
            print(f"⚠️ Ollama summary generation failed: {e}")
            return self._fallback_news_summary(news_items, high_priority_news)
    
    def _fallback_news_summary(self, news_items, high_priority_news):
        """Fallback news-focused summary when Ollama fails"""
        summary = f"## 📰 Weekly Competitor News Digest\n\n"
        
        summary += f"### 🔥 Top Stories This Week\n"
        if high_priority_news:
            for item in high_priority_news[:3]:
                summary += f"• **{item['competitor']}**: {item['title']}\n"
                summary += f"  _{item['excerpt'][:80]}..._\n\n"
        else:
            summary += "• No high-priority news items this week\n\n"
        
        summary += f"### 📊 Market Intelligence Summary\n"
        summary += f"This week we tracked {len(news_items)} news items and updates across "
        summary += f"{len(set(item['competitor'] for item in news_items))} competitors. "
        
        if len(high_priority_news) > 3:
            summary += f"We detected {len(high_priority_news)} high-priority developments requiring attention.\n\n"
        elif len(high_priority_news) > 0:
            summary += f"We identified {len(high_priority_news)} important updates worth monitoring.\n\n"
        else:
            summary += "Most activity was routine updates and minor changes.\n\n"
        
        summary += f"### 📈 Most Active Competitors\n"
        competitor_activity = {}
        for item in news_items:
            competitor_activity[item['competitor']] = competitor_activity.get(item['competitor'], 0) + 1
        
        sorted_activity = sorted(competitor_activity.items(), key=lambda x: x[1], reverse=True)
        for competitor, count in sorted_activity[:3]:
            summary += f"• **{competitor}**: {count} news items\n"
        
        summary += f"\n### 💡 Strategic Insights\n"
        if len(high_priority_news) > 2:
            summary += "• High competitor activity suggests increased market competition\n"
            summary += "• Monitor for potential market shifts and new opportunities\n"
        else:
            summary += "• Stable competitive environment with routine updates\n"
            summary += "• Good opportunity to focus on internal product development\n"
        
        summary += f"• Continue monitoring for emerging trends and strategic moves"
        
        return summary
    
    def _call_ollama(self, prompt):
        """Call Ollama with the given prompt"""
        try:
            process = subprocess.Popen(
                ['ollama', 'run', self.model],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            stdout, stderr = process.communicate(prompt, timeout=60)
            
            if process.returncode == 0:
                return self._clean_ollama_response(stdout)
            else:
                raise Exception(f"Ollama error: {stderr}")
                
        except subprocess.TimeoutExpired:
            process.kill()
            raise Exception("Ollama timeout")
        except FileNotFoundError:
            raise Exception("Ollama not found. Please install Ollama first.")
    
    def _clean_ollama_response(self, response):
        """Clean and format Ollama response"""
        lines = response.strip().split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('>>>') and not line.startswith('...'):
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _parse_enhanced_response(self, response, website):
        """Parse structured Ollama response"""
        try:
            lines = response.split('\n')
            result = {
                'change_type': "content_update",
                'importance_score': 5,
                'analysis': "Content changes detected",
                'news_title': "Website Update Detected",
                'news_excerpt': "Changes identified in competitor website",
                'source_links': website
            }
            
            for line in lines:
                if line.startswith('CHANGE_TYPE:'):
                    result['change_type'] = line.split(':', 1)[1].strip()
                elif line.startswith('IMPORTANCE:'):
                    try:
                        result['importance_score'] = int(line.split(':', 1)[1].strip())
                    except:
                        result['importance_score'] = 5
                elif line.startswith('NEWS_TITLE:'):
                    result['news_title'] = line.split(':', 1)[1].strip()
                elif line.startswith('NEWS_EXCERPT:'):
                    result['news_excerpt'] = line.split(':', 1)[1].strip()
                elif line.startswith('ANALYSIS:'):
                    result['analysis'] = line.split(':', 1)[1].strip()
            
            return result
                
        except Exception as e:
            print(f"Error parsing Ollama response: {e}")
            return {
                'change_type': "content_update",
                'importance_score': 5,
                'analysis': response[:200] if response else "Analysis failed",
                'news_title': "Website Changes Detected",
                'news_excerpt': "AI analysis completed",
                'source_links': website
            }

class CompetitorTracker:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.ai = OllamaAI()
        self.pdf_generator = PDFGenerator()
    
    def get_content_hash(self, content):
        """Generate hash for content comparison"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def scrape_website(self, url):
        """Enhanced website scraping with better content extraction"""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                element.decompose()
            
            # Extract main content
            main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile(r'content|main'))
            if main_content:
                text = main_content.get_text()
            else:
                text = soup.get_text()
            
            # Clean text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            clean_text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Look for changelog/release notes
            changelog_content = self._extract_changelog_content(soup, clean_text)
            
            return {
                'url': url,
                'title': soup.title.string if soup.title else 'No title',
                'content': clean_text[:5000],  # Increased limit for better analysis
                'changelog_content': changelog_content,
                'content_hash': self.get_content_hash(clean_text),
                'scraped_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'url': url,
                'error': str(e),
                'scraped_at': datetime.now().isoformat()
            }
    
    def _extract_changelog_content(self, soup, text):
        """Enhanced changelog extraction"""
        changelog_indicators = [
            'changelog', 'release notes', 'what\'s new', 'updates', 
            'version', 'releases', 'news', 'announcements', 'blog'
        ]
        
        # Look for dedicated changelog sections
        for indicator in changelog_indicators:
            changelog_section = soup.find(['div', 'section'],
                                        class_=re.compile(indicator, re.I))
            if changelog_section:
                return changelog_section.get_text()[:2000]
        
        # Fallback to text search
        changelog_content = ""
        for indicator in changelog_indicators:
            if indicator.lower() in text.lower():
                pattern = rf'.{{0,400}}{re.escape(indicator)}.{{0,1000}}'
                matches = re.findall(pattern, text, re.IGNORECASE)
                changelog_content += ' '.join(matches)
        
        return changelog_content[:2000]
    
    def analyze_changes_with_ai(self, competitor_id, current_data):
        """Enhanced change analysis with AI and database storage"""
        conn = sqlite3.connect('competitor_tracker.db')
        cursor = conn.cursor()
        
        # Get competitor info
        cursor.execute('SELECT name, website FROM competitors WHERE id = ?', (competitor_id,))
        competitor = cursor.fetchone()
        if not competitor:
            conn.close()
            return None
        
        competitor_name, website = competitor
        
        # Get last content snapshot
        cursor.execute('''
            SELECT full_content FROM content_snapshots 
            WHERE competitor_id = ? 
            ORDER BY scraped_at DESC LIMIT 1
        ''', (competitor_id,))
        
        last_snapshot = cursor.fetchone()
        previous_content = last_snapshot[0] if last_snapshot else ""
        
        # Save current snapshot
        cursor.execute('''
            INSERT INTO content_snapshots (competitor_id, content_hash, full_content, scraped_at)
            VALUES (?, ?, ?, ?)
        ''', (competitor_id, current_data['content_hash'], current_data['content'], current_data['scraped_at']))
        
        # AI Analysis
        if current_data.get('content'):
            ai_result = self.ai.analyze_content_changes(
                previous_content, current_data['content'], competitor_name, website
            )
        else:
            ai_result = {
                'analysis': "Failed to scrape content",
                'change_type': "error",
                'importance_score': 1,
                'news_title': f"Scan Error for {competitor_name}",
                'news_excerpt': "Unable to retrieve website content",
                'source_links': website
            }
        
        # Save enhanced change record
        change_record = {
            'competitor_id': competitor_id,
            'competitor_name': competitor_name,
            'content': current_data['content'],
            'content_hash': current_data['content_hash'],
            'changelog_content': current_data.get('changelog_content', ''),
            'analysis': ai_result['analysis'],
            'change_type': ai_result['change_type'],
            'importance_score': ai_result['importance_score'],
            'news_title': ai_result['news_title'],
            'news_excerpt': ai_result['news_excerpt'],
            'source_links': ai_result['source_links'],
            'detected_at': current_data['scraped_at'],
            'url': website
        }
        
        cursor.execute('''
            INSERT INTO changes (
                competitor_id, competitor_name, content, content_hash, 
                changelog_content, analysis, detected_at, url, change_type,
                importance_score, news_title, news_excerpt, source_links
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            change_record['competitor_id'], change_record['competitor_name'],
            change_record['content'], change_record['content_hash'],
            change_record['changelog_content'], change_record['analysis'],
            change_record['detected_at'], change_record['url'],
            change_record['change_type'], change_record['importance_score'],
            change_record['news_title'], change_record['news_excerpt'],
            change_record['source_links']
        ))
        
        # Update competitor last_checked
        cursor.execute('''
            UPDATE competitors SET last_checked = ? WHERE id = ?
        ''', (current_data['scraped_at'], competitor_id))
        
        conn.commit()
        conn.close()
        
        return change_record

# Initialize tracker
tracker = CompetitorTracker()

# Database helper functions with backward compatibility
def get_competitors():
    """Get all competitors from database"""
    conn = sqlite3.connect('competitor_tracker.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM competitors ORDER BY name')
    competitors = []
    for row in cursor.fetchall():
        competitors.append({
            'id': row[0], 'name': row[1], 'website': row[2],
            'changelog_url': row[3] if len(row) > 3 else '',
            'added_at': row[4] if len(row) > 4 else '',
            'last_checked': row[5] if len(row) > 5 else None,
            'status': row[6] if len(row) > 6 else 'active'
        })
    conn.close()
    return competitors

def get_recent_changes(limit=50):
    """Get recent changes from database with backward compatibility"""
    conn = sqlite3.connect('competitor_tracker.db')
    cursor = conn.cursor()
    
    # First check what columns exist
    cursor.execute("PRAGMA table_info(changes)")
    columns = [row[1] for row in cursor.fetchall()]
    
    cursor.execute('''
        SELECT * FROM changes 
        ORDER BY detected_at DESC 
        LIMIT ?
    ''', (limit,))
    
    changes = []
    for row in cursor.fetchall():
        change = {
            'id': row[0] if len(row) > 0 else 0,
            'competitor_id': row[1] if len(row) > 1 else 0,
            'competitor_name': row[2] if len(row) > 2 else 'Unknown',
            'content': row[3] if len(row) > 3 else '',
            'content_hash': row[4] if len(row) > 4 else '',
            'changelog_content': row[5] if len(row) > 5 else '',
            'analysis': row[6] if len(row) > 6 else 'No analysis',
            'ai_summary': row[7] if len(row) > 7 else '',
            'detected_at': row[8] if len(row) > 8 else '',
            'url': row[9] if len(row) > 9 else '',
            'change_type': row[10] if len(row) > 10 else 'unknown',
            'importance_score': row[11] if len(row) > 11 else 5,
            # New fields with fallback
            'news_title': row[12] if len(row) > 12 else f"Update from {row[2] if len(row) > 2 else 'Unknown'}",
            'news_excerpt': row[13] if len(row) > 13 else (row[6] if len(row) > 6 else 'No details available')[:100],
            'source_links': row[14] if len(row) > 14 else (row[9] if len(row) > 9 else '')
        }
        changes.append(change)
    
    conn.close()
    return changes

def get_settings():
    """Get settings from database"""
    conn = sqlite3.connect('competitor_tracker.db')
    cursor = conn.cursor()
    cursor.execute('SELECT key, value FROM settings')
    settings = {}
    for row in cursor.fetchall():
        settings[row[0]] = row[1]
    conn.close()
    
    # Default settings
    default_settings = {
        'slack_webhook': '',
        'notion_token': '',
        'scan_frequency': '5min',
        'auto_scan_enabled': 'true'
    }
    
    for key, value in default_settings.items():
        if key not in settings:
            settings[key] = value
    
    return settings

def get_company_profile():
    """Get company profile from database"""
    conn = sqlite3.connect('competitor_tracker.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM company_profile ORDER BY created_at DESC LIMIT 1')
    profile = cursor.fetchone()
    conn.close()
    
    if profile:
        return {
            'id': profile[0],
            'name': profile[1],
            'website': profile[2],
            'description': profile[3],
            'industry': profile[4],
            'founded_year': profile[5],
            'size': profile[6],
            'headquarters': profile[7],
            'key_products': profile[8],
            'target_market': profile[9],
            'competitive_advantages': profile[10],
            'created_at': profile[11],
            'updated_at': profile[12]
        }
    return None

def get_company_updates(limit=20):
    """Get company updates from database"""
    conn = sqlite3.connect('competitor_tracker.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM company_updates ORDER BY date_published DESC LIMIT ?', (limit,))
    updates = []
    for row in cursor.fetchall():
        updates.append({
            'id': row[0],
            'title': row[1],
            'content': row[2],
            'update_type': row[3],
            'importance_score': row[4],
            'date_published': row[5],
            'source_url': row[6],
            'tags': row[7],
            'created_at': row[8]
        })
    conn.close()
    return updates

def get_competitive_insights():
    """Get competitive insights from database"""
    conn = sqlite3.connect('competitor_tracker.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM competitive_insights ORDER BY created_at DESC LIMIT 10')
    insights = []
    for row in cursor.fetchall():
        insights.append({
            'id': row[0],
            'competitor_id': row[1],
            'insight_type': row[2],
            'insight_content': row[3],
            'impact_level': row[4],
            'recommendation': row[5],
            'created_at': row[6]
        })
    conn.close()
    return insights

# Flask Routes
@app.route('/')
def home():
    try:
        competitors = get_competitors()
        recent_changes = get_recent_changes(20)
        return render_template('home.html', competitors=competitors, recent_changes=recent_changes)
    except Exception as e:
        print(f"Error in home route: {e}")
        return f"Error loading page: {e}", 500

@app.route('/dashboard')
def dashboard():
    try:
        competitors = get_competitors()
        changes = get_recent_changes(100)
        settings = get_settings()
        return render_template('page1.html',
                             competitors=competitors,
                             changes=changes,
                            settings=settings)
    except Exception as e:
        print(f"Error in dashboard route: {e}")
        return f"Error loading dashboard: {e}", 500

@app.route('/comparison')
def comparison():
    try:
        competitors = get_competitors()
        changes = get_recent_changes(100)
        company_profile = get_company_profile()
        company_updates = get_company_updates()
        
        # Get competitive insights if company profile exists
        competitive_insights = None
        if company_profile:
            try:
                competitive_insights = get_competitive_insights()
            except:
                competitive_insights = None
        
        return render_template('comparison.html',
                             competitors=competitors,
                             changes=changes,
                             company_profile=company_profile,
                             company_updates=company_updates,
                             competitive_insights=competitive_insights)
    except Exception as e:
        print(f"Error in comparison route: {e}")
        return f"Error loading comparison: {e}", 500

@app.route('/add_competitor', methods=['POST'])
def add_competitor():
    try:
        data = request.get_json()
        
        conn = sqlite3.connect('competitor_tracker.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO competitors (name, website, changelog_url, added_at, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (data['name'], data['website'], data.get('changelog_url', ''),
              datetime.now().isoformat(), 'active'))
        
        competitor_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'competitor_id': competitor_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/save_company_profile', methods=['POST'])
def save_company_profile():
    try:
        data = request.get_json()
        print(f"📝 Received company profile data: {data}")
        
        # Validate required fields
        if not data.get('name') or not data.get('industry'):
            return jsonify({'error': 'Name and Industry are required fields'}), 400
        
        conn = sqlite3.connect('competitor_tracker.db')
        cursor = conn.cursor()
        
        # Check if profile exists
        cursor.execute('SELECT id FROM company_profile LIMIT 1')
        existing = cursor.fetchone()
        
        current_time = datetime.now().isoformat()
        
        if existing:
            # Update existing profile
            cursor.execute('''
                UPDATE company_profile SET
                name = ?, website = ?, description = ?, industry = ?,
                founded_year = ?, size = ?, headquarters = ?, key_products = ?,
                target_market = ?, competitive_advantages = ?, updated_at = ?
                WHERE id = ?
            ''', (
                data['name'], 
                data.get('website', ''), 
                data.get('description', ''),
                data['industry'], 
                data.get('founded_year') if data.get('founded_year') else None, 
                data.get('size', ''),
                data.get('headquarters', ''), 
                data.get('key_products', ''),
                data.get('target_market', ''), 
                data.get('competitive_advantages', ''),
                current_time, 
                existing[0]
            ))
            print(f"✅ Updated company profile for {data['name']}")
        else:
            # Create new profile
            cursor.execute('''
                INSERT INTO company_profile (
                    name, website, description, industry, founded_year, size,
                    headquarters, key_products, target_market, competitive_advantages,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['name'], 
                data.get('website', ''), 
                data.get('description', ''),
                data['industry'], 
                data.get('founded_year') if data.get('founded_year') else None, 
                data.get('size', ''),
                data.get('headquarters', ''), 
                data.get('key_products', ''),
                data.get('target_market', ''), 
                data.get('competitive_advantages', ''),
                current_time, 
                current_time
            ))
            print(f"✅ Created new company profile for {data['name']}")
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Company profile saved successfully'})
    except Exception as e:
        print(f"❌ Error saving company profile: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/add_company_update', methods=['POST'])
def add_company_update():
    try:
        data = request.get_json()
        print(f"📢 Received company update data: {data}")
        
        # Validate required fields
        if not data.get('title') or not data.get('update_type'):
            return jsonify({'error': 'Title and Update Type are required fields'}), 400
        
        conn = sqlite3.connect('competitor_tracker.db')
        cursor = conn.cursor()
        
        # Set default date if not provided
        date_published = data.get('date_published')
        if not date_published:
            date_published = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO company_updates (
                title, content, update_type, importance_score, date_published,
                source_url, tags, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['title'], 
            data.get('content', ''), 
            data['update_type'],
            data.get('importance_score', 5), 
            date_published,
            data.get('source_url', ''), 
            data.get('tags', ''), 
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Added company update: {data['title']}")
        return jsonify({'success': True, 'message': 'Company update added successfully'})
    except Exception as e:
        print(f"❌ Error adding company update: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/delete_company_update/<int:update_id>', methods=['DELETE'])
def delete_company_update(update_id):
    try:
        conn = sqlite3.connect('competitor_tracker.db')
        cursor = conn.cursor()
        
        # Delete the update
        cursor.execute('DELETE FROM company_updates WHERE id = ?', (update_id,))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'error': 'Update not found'}), 404
        
        conn.commit()
        conn.close()
        
        print(f"✅ Deleted company update with ID: {update_id}")
        return jsonify({'success': True, 'message': 'Company update deleted successfully'})
    except Exception as e:
        print(f"❌ Error deleting company update: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/clear_all_company_updates', methods=['DELETE'])
def clear_all_company_updates():
    try:
        conn = sqlite3.connect('competitor_tracker.db')
        cursor = conn.cursor()
        
        # Delete all company updates
        cursor.execute('DELETE FROM company_updates')
        deleted_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        print(f"✅ Cleared all company updates ({deleted_count} deleted)")
        return jsonify({'success': True, 'message': f'All {deleted_count} company updates cleared successfully'})
    except Exception as e:
        print(f"❌ Error clearing company updates: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/generate_competitive_insights')
def generate_competitive_insights():
    try:
        # Get company profile
        company_profile = get_company_profile()
        if not company_profile:
            return jsonify({'error': 'Company profile not found. Please set up your company profile first.'}), 400
        
        # Get recent competitor changes (last 30 days)
        month_ago = datetime.now() - timedelta(days=30)
        
        conn = sqlite3.connect('competitor_tracker.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM changes 
            WHERE datetime(detected_at) > datetime(?)
            ORDER BY importance_score DESC, detected_at DESC
        ''', (month_ago.isoformat(),))
        
        recent_changes = []
        for row in cursor.fetchall():
            change = {
                'competitor_name': row[2] if len(row) > 2 else 'Unknown',
                'analysis': row[6] if len(row) > 6 else 'No analysis',
                'detected_at': row[8] if len(row) > 8 else '',
                'change_type': row[10] if len(row) > 10 else 'unknown',
                'importance_score': row[11] if len(row) > 11 else 5,
                'news_title': row[12] if len(row) > 12 else 'Update',
                'news_excerpt': row[13] if len(row) > 13 else ''
            }
            recent_changes.append(change)
        
        # Generate AI insights with industry-specific research
        try:
            insights = tracker.ai.generate_competitive_insights(company_profile, recent_changes)
            
            # Save insights to database
            cursor.execute('''
                INSERT INTO competitive_insights (
                    competitor_id, insight_type, insight_content, impact_level, 
                    recommendation, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                0,  # General insight, not competitor-specific
                'competitive_analysis',
                insights,
                'high',
                'Strategic recommendations included in analysis',
                datetime.now().isoformat()
            ))
            conn.commit()
            
        except Exception as e:
            print(f"AI insights generation failed: {e}")
            insights = f"Competitive analysis of {len(recent_changes)} competitor changes detected in the last 30 days."
        
        conn.close()
        
        return jsonify({
            'insights': insights,
            'changes_analyzed': len(recent_changes),
            'company_name': company_profile.get('name', 'Your Company')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/remove_competitor/<int:competitor_id>', methods=['DELETE'])
def remove_competitor(competitor_id):
    try:
        conn = sqlite3.connect('competitor_tracker.db')
        cursor = conn.cursor()
        
        # Remove competitor and related data
        cursor.execute('DELETE FROM competitors WHERE id = ?', (competitor_id,))
        cursor.execute('DELETE FROM changes WHERE competitor_id = ?', (competitor_id,))
        cursor.execute('DELETE FROM content_snapshots WHERE competitor_id = ?', (competitor_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/scan_competitor/<int:competitor_id>')
def scan_competitor(competitor_id):
    try:
        conn = sqlite3.connect('competitor_tracker.db')
        cursor = conn.cursor()
        cursor.execute('SELECT website FROM competitors WHERE id = ?', (competitor_id,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return jsonify({'error': 'Competitor not found'}), 404
        
        website = result[0]
        
        # Scrape current content
        current_data = tracker.scrape_website(website)
        
        if current_data.get('error'):
            return jsonify({'error': current_data['error']})
        
        # Analyze changes with AI
        change_record = tracker.analyze_changes_with_ai(competitor_id, current_data)
        
        if change_record:
            return jsonify({'success': True, 'change': change_record})
        else:
            return jsonify({'error': 'Failed to analyze changes'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/scan_all')
def scan_all():
    try:
        competitors = get_competitors()
        results = []
        
        for competitor in competitors: 
            try:
                # Scrape website
                current_data = tracker.scrape_website(competitor['website'])
                
                if current_data.get('error'):
                    results.append({'error': current_data['error'], 'competitor': competitor['name']})
                    continue
                
                # Analyze with AI
                change_record = tracker.analyze_changes_with_ai(competitor['id'], current_data)
                results.append({'success': True, 'competitor': competitor['name'], 'change': change_record})
                
            except Exception as e:
                results.append({'error': str(e), 'competitor': competitor['name']})
        
        return jsonify({'results': results})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generate_summary')
def generate_summary():
    try:
        # Get changes from last week
        week_ago = datetime.now() - timedelta(days=7)
        
        conn = sqlite3.connect('competitor_tracker.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM changes 
            WHERE datetime(detected_at) > datetime(?)
            ORDER BY importance_score DESC, detected_at DESC
        ''', (week_ago.isoformat(),))
        
        recent_changes = []
        for row in cursor.fetchall():
            change = {
                'id': row[0] if len(row) > 0 else 0,
                'competitor_id': row[1] if len(row) > 1 else 0,
                'competitor_name': row[2] if len(row) > 2 else 'Unknown',
                'analysis': row[6] if len(row) > 6 else 'No analysis',
                'detected_at': row[8] if len(row) > 8 else '',
                'url': row[9] if len(row) > 9 else '',
                'change_type': row[10] if len(row) > 10 else 'unknown',
                'importance_score': row[11] if len(row) > 11 else 5,
                'news_title': row[12] if len(row) > 12 else f"Update from {row[2] if len(row) > 2 else 'Unknown'}",
                'news_excerpt': row[13] if len(row) > 13 else '',
                'source_links': row[14] if len(row) > 14 else ''
            }
            recent_changes.append(change)
        
        conn.close()
        
        if not recent_changes:
            return jsonify({'summary': 'No changes detected in the past week.', 'changes_count': 0})
        
        # Generate AI summary
        try:
            ai_summary = tracker.ai.generate_weekly_summary(recent_changes)
        except Exception as e:
            print(f"AI summary failed: {e}")
            ai_summary = f"Weekly Summary: {len(recent_changes)} changes detected across competitors."
        
        return jsonify({
            'summary': ai_summary, 
            'changes_count': len(recent_changes),
            'changes_data': recent_changes
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generate_pdf_report')
def generate_pdf_report():
    """Generate comprehensive PDF report"""
    try:
        # Get recent changes (last 30 days for comprehensive report)
        month_ago = datetime.now() - timedelta(days=30)
        
        conn = sqlite3.connect('competitor_tracker.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM changes 
            WHERE datetime(detected_at) > datetime(?)
            ORDER BY importance_score DESC, detected_at DESC
        ''', (month_ago.isoformat(),))
        
        changes_data = []
        for row in cursor.fetchall():
            change = {
                'id': row[0] if len(row) > 0 else 0,
                'competitor_name': row[2] if len(row) > 2 else 'Unknown',
                'analysis': row[6] if len(row) > 6 else 'No analysis',
                'detected_at': row[8] if len(row) > 8 else '',
                'url': row[9] if len(row) > 9 else '',
                'change_type': row[10] if len(row) > 10 else 'unknown',
                'importance_score': row[11] if len(row) > 11 else 5,
                'news_title': row[12] if len(row) > 12 else f"Update from {row[2] if len(row) > 2 else 'Unknown'}",
                'news_excerpt': row[13] if len(row) > 13 else '',
                'source_links': row[14] if len(row) > 14 else ''
            }
            changes_data.append(change)
        
        conn.close()
        
        # Generate AI summary for the report
        try:
            ai_summary = tracker.ai.generate_weekly_summary(changes_data)
        except:
            ai_summary = f"Comprehensive analysis of {len(changes_data)} competitor changes detected in the last 30 days."
        
        # Generate PDF
        pdf_buffer = tracker.pdf_generator.generate_comprehensive_report(changes_data, ai_summary)
        
        if not pdf_buffer:
            return jsonify({'error': 'PDF generation failed - ReportLab not available'}), 500
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_file.write(pdf_buffer.getvalue())
        temp_file.close()
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"AI_Competitor_Intelligence_Report_{timestamp}.pdf"
        
        return send_file(
            temp_file.name,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        return jsonify({'error': f'Failed to generate PDF report: {str(e)}'}), 500

@app.route('/settings', methods=['GET', 'POST'])
def manage_settings():
    try:
        if request.method == 'POST':
            data = request.get_json()
            
            conn = sqlite3.connect('competitor_tracker.db')
            cursor = conn.cursor()
            
            for key, value in data.items():
                cursor.execute('''
                    INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)
                ''', (key, value))
            
            conn.commit()
            conn.close()
            
            return jsonify({'success': True})
        
        return jsonify(get_settings())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/send_to_slack', methods=['POST'])
def send_to_slack():
    try:
        settings = get_settings()
        
        if not settings.get('slack_webhook'):
            return jsonify({'error': 'Slack webhook not configured'}), 400
        
        summary_response = generate_summary()
        summary_data = summary_response.get_json()
        
        slack_payload = {
            'text': '📰 Weekly Competitor News Digest',
            'blocks': [
                {
                    'type': 'section',
                    'text': {
                        'type': 'mrkdwn',
                        'text': f"*📰 Weekly Competitor News Digest*\n\n{summary_data['summary']}"
                    }
                },
                {
                    'type': 'context',
                    'elements': [
                        {
                            'type': 'mrkdwn',
                            'text': f"📊 {summary_data['changes_count']} news items analyzed | 🧠 Generated by AI"
                        }
                    ]
                }
            ]
        }
        
        response = requests.post(settings['slack_webhook'], json=slack_payload)
        response.raise_for_status()
        return jsonify({'success': True, 'message': 'Competitor news digest sent to Slack'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def run_scheduled_scans():
    """Background task for scheduled scanning every 5 minutes"""
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

def auto_scan_all():
    """Auto scan function for scheduler"""
    print(f"🤖 Auto-scanning all competitors at {datetime.now()}")
    try:
        competitors = get_competitors()
        for competitor in competitors: 
            try:
                current_data = tracker.scrape_website(competitor['website'])
                if not current_data.get('error'):
                    tracker.analyze_changes_with_ai(competitor['id'], current_data)
                time.sleep(2)  # Small delay between scans
            except Exception as e:
                print(f"Error scanning {competitor['name']}: {e}")
        print(f"✅ Auto-scan completed at {datetime.now()}")
    except Exception as e:
        print(f"❌ Auto-scan failed: {e}")

# Schedule scans every 5 minutes
schedule.every(5).minutes.do(auto_scan_all)

# Start background scheduler
scheduler_thread = threading.Thread(target=run_scheduled_scans, daemon=True)
scheduler_thread.start()

if __name__ == '__main__':
    print("🚀 Starting AI-Powered Competitor Tracker...")   
    print("📊 Database initialized and migrated")
    print("🧠 Ollama AI integration ready")
    print("📄 PDF report generation enabled")
    print("⏰ Auto-scanning every 5 minutes")
    print("🔍 Enhanced monitoring system active")
    print("🆚 Company comparison feature enabled")
    print("🌐 Server starting on http://localhost:5000")
    app.run(port=5000)
