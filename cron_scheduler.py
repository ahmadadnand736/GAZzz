import schedule
import time
import threading
import json
import os
from datetime import datetime, timedelta
from article_generator import ArticleGenerator
from cloudflare_worker import CloudflareWorkerManager

class CronScheduler:
    def __init__(self):
        self.is_running = False
        self.scheduler_thread = None
        self.article_generator = ArticleGenerator()
        self.worker_manager = CloudflareWorkerManager()
        self.load_config()
    
    def load_config(self):
        """Load scheduler configuration"""
        try:
            with open('scheduler_config.json', 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            self.config = {
                "schedule_hours": [8, 12, 16, 20],
                "timezone": "Asia/Jakarta",
                "max_articles_per_run": 3,
                "enabled": False
            }
            self.save_config()
    
    def save_config(self):
        """Save scheduler configuration"""
        with open('scheduler_config.json', 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def set_schedule(self, hours, timezone="Asia/Jakarta", max_articles=3):
        """Set schedule configuration"""
        self.config.update({
            "schedule_hours": hours,
            "timezone": timezone,
            "max_articles_per_run": max_articles,
            "enabled": True
        })
        self.save_config()
        
        # Clear existing schedules
        schedule.clear()
        
        # Set new schedules
        for hour in hours:
            schedule.every().day.at(f"{hour:02d}:00").do(self.run_article_generation)
        
        return True
    
    def run_article_generation(self):
        """Run article generation process"""
        try:
            print(f"Starting article generation at {datetime.now()}")
            
            # Get random subjects
            subjects = self.article_generator.get_random_subjects(self.config["max_articles_per_run"])
            
            # Generate articles
            generated_articles = []
            for subject in subjects:
                article = self.article_generator.generate_article(subject)
                if article:
                    generated_articles.append(article)
                    print(f"Generated: {article['title']}")
            
            # Update worker if articles were generated
            if generated_articles:
                self.worker_manager.deploy_worker()
                print(f"Successfully generated {len(generated_articles)} articles and updated worker")
            
            # Log activity
            self.log_activity(f"Generated {len(generated_articles)} articles")
            
            return generated_articles
            
        except Exception as e:
            print(f"Error in article generation: {str(e)}")
            self.log_activity(f"Error: {str(e)}")
            return []
    
    def log_activity(self, message):
        """Log scheduler activity"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "message": message
        }
        
        # Load existing logs
        try:
            with open('scheduler_logs.json', 'r') as f:
                logs = json.load(f)
        except FileNotFoundError:
            logs = []
        
        # Add new log entry
        logs.append(log_entry)
        
        # Keep only last 100 entries
        if len(logs) > 100:
            logs = logs[-100:]
        
        # Save logs
        with open('scheduler_logs.json', 'w') as f:
            json.dump(logs, f, indent=2)
    
    def start(self):
        """Start the scheduler"""
        if self.is_running:
            return False
        
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        self.log_activity("Scheduler started")
        return True
    
    def stop(self):
        """Stop the scheduler"""
        self.is_running = False
        schedule.clear()
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=1)
        
        self.log_activity("Scheduler stopped")
        return True
    
    def _run_scheduler(self):
        """Internal scheduler loop"""
        while self.is_running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def get_next_run(self):
        """Get next scheduled run time"""
        if not schedule.jobs:
            return None
        
        next_run = schedule.next_run()
        if next_run:
            return next_run.strftime('%Y-%m-%d %H:%M:%S')
        return None
    
    def get_status(self):
        """Get scheduler status"""
        return {
            "is_running": self.is_running,
            "next_run": self.get_next_run(),
            "config": self.config,
            "jobs_count": len(schedule.jobs)
        }
    
    def get_logs(self, limit=20):
        """Get scheduler logs"""
        try:
            with open('scheduler_logs.json', 'r') as f:
                logs = json.load(f)
                return logs[-limit:] if limit else logs
        except FileNotFoundError:
            return []
    
    def manual_run(self):
        """Manually trigger article generation"""
        if not self.is_running:
            return {"success": False, "message": "Scheduler is not running"}
        
        try:
            articles = self.run_article_generation()
            return {
                "success": True,
                "message": f"Generated {len(articles)} articles",
                "articles": articles
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            }
    
    def update_subjects_file(self, subjects):
        """Update subjects file with new topics"""
        try:
            with open('subjects.txt', 'w', encoding='utf-8') as f:
                for subject in subjects:
                    f.write(f"{subject}\n")
            
            self.log_activity(f"Updated subjects file with {len(subjects)} topics")
            return True
        except Exception as e:
            self.log_activity(f"Error updating subjects: {str(e)}")
            return False
    
    def get_subjects(self):
        """Get current subjects from file"""
        try:
            with open('subjects.txt', 'r', encoding='utf-8') as f:
                return [line.strip() for line in f.readlines() if line.strip()]
        except FileNotFoundError:
            return []
    
    def add_subject(self, subject):
        """Add a new subject to the list"""
        subjects = self.get_subjects()
        if subject not in subjects:
            subjects.append(subject)
            self.update_subjects_file(subjects)
            self.log_activity(f"Added new subject: {subject}")
            return True
        return False
    
    def remove_subject(self, subject):
        """Remove a subject from the list"""
        subjects = self.get_subjects()
        if subject in subjects:
            subjects.remove(subject)
            self.update_subjects_file(subjects)
            self.log_activity(f"Removed subject: {subject}")
            return True
        return False