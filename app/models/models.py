from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from enum import Enum
import json
from flask_login import UserMixin

class TypeScript(Enum):
    NODE_EXPORTER = "node_exporter"
    PROMTAIL = "promtail"
    LOKI = "loki"

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20))
    email = db.Column(db.String(120), unique=True)
    
    # Relationships
    nodes = db.relationship('Node', backref='owner', lazy='dynamic')
    access_logs = db.relationship('AccessLog', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password, password)
    
    def register(self):
        db.session.add(self)
        db.session.commit()
    
    def login(self, username, password):
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            return user
        return None
    
    def updateProfile(self, username=None, email=None):
        if username:
            self.username = username
        if email:
            self.email = email
        db.session.commit()
    
    def deleteAccount(self, id):
        user = User.query.get(id)
        if user:
            db.session.delete(user)
            db.session.commit()
            return True
        return False

class Node(db.Model):
    __tablename__ = 'nodes'

    id = db.Column(db.Integer, primary_key=True)
    ownerId = db.Column(db.Integer, db.ForeignKey('users.id'))
    name = db.Column(db.String(100))
    status = db.Column(db.String(20))
    ipAddress = db.Column(db.String(50))
    portNodeExporter = db.Column(db.Integer)
    portPromtail = db.Column(db.Integer)
    
    # Relationships
    performance_data = db.relationship('PerformanceData', backref='node', lazy='dynamic')
    onchain_data = db.relationship('OnchainData', backref='node', lazy='dynamic')
    alerts = db.relationship('Alert', backref='node', lazy='dynamic')
    reports = db.relationship('Report', backref='node', lazy='dynamic')
    web_displays = db.relationship('WebDisplay', backref='node', lazy='dynamic')
    script_generators = db.relationship('ScriptGenerator', backref='node', lazy='dynamic')
    data_collection_configs = db.relationship('DataCollectionConfig', backref='node', lazy='dynamic')
    
    @classmethod
    def get_nodes_by_user(cls, user_id, search=None, status=None):
        """Get all nodes for a user with optional filters"""
        query = cls.query.filter_by(ownerId=user_id)
        
        if search:
            query = query.filter(cls.name.ilike(f'%{search}%'))
        if status and status != 'all':
            query = query.filter_by(status=status)
            
        return query.all()

    def update_node(self, data):
        """Update node with new data"""
        try:
            self.name = data.get('name', self.name)
            self.ipAddress = data.get('ipAddress', self.ipAddress)
            self.portNodeExporter = data.get('portNodeExporter', self.portNodeExporter)
            self.portPromtail = data.get('portPromtail', self.portPromtail)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to update node: {str(e)}")

    @classmethod
    def create_node(cls, owner_id, data):
        """Create a new node"""
        try:
            new_node = cls(
                ownerId=owner_id,
                name=data.get('name'),
                ipAddress=data.get('ipAddress'),
                portNodeExporter=data.get('portNodeExporter'),
                portPromtail=data.get('portPromtail'),
                status=data.get('status', 'inactive')
            )
            db.session.add(new_node)
            db.session.commit()
            return new_node
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to create node: {str(e)}")

    def delete_node(self):
        """Delete this node"""
        try:
            db.session.delete(self)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to delete node: {str(e)}")

    def to_dict(self):
        """Convert node to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'ipAddress': self.ipAddress,
            'status': self.status,
            'portNodeExporter': self.portNodeExporter,
            'portPromtail': self.portPromtail
        }

class AccessLog(db.Model):
    __tablename__ = 'access_logs'

    id = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer, db.ForeignKey('users.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    action = db.Column(db.String(100))
    
    def logAccess(self, userId, action):
        pass
    
    def getAccessStatus(self, userId):
        return AccessLog

class DataCollectionConfig(db.Model):
    __tablename__ = 'data_collection_configs'

    id = db.Column(db.Integer, primary_key=True)
    nodeId = db.Column(db.Integer, db.ForeignKey('nodes.id'))
    dataSources = db.Column(db.String(500))  # JSON string representing Map<String, Map<String, boolean>>
    
    def configureCollection(self, id, source):
        pass
    
    def getCollectionConfig(self, id):
        return {}  # Map<String, Map<String, boolean>>

class OnchainData(db.Model):
    __tablename__ = 'onchain_data'

    id = db.Column(db.Integer, primary_key=True)
    nodeId = db.Column(db.Integer, db.ForeignKey('nodes.id'))
    blockHeight = db.Column(db.Integer)
    transactionCount = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def queryOnchainData(self, nodeId):
        return OnchainData
    
    def storeOnchainData(self):
        pass

class PerformanceData(db.Model):
    __tablename__ = 'performance_data'

    id = db.Column(db.Integer, primary_key=True)
    nodeId = db.Column(db.Integer, db.ForeignKey('nodes.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    cpuUsage = db.Column(db.Float)
    memoryUsage = db.Column(db.Float)
    diskUsage = db.Column(db.Float)
    networkUpUsage = db.Column(db.Float)
    networkDownUsage = db.Column(db.Float)
    uptime = db.Column(db.Float)
    
    def fetchPerformanceData(self, nodeId):
        return PerformanceData
    
    def storePerformanceData(self):
        pass

class Alert(db.Model):
    __tablename__ = 'alerts'

    id = db.Column(db.Integer, primary_key=True)
    nodeId = db.Column(db.Integer, db.ForeignKey('nodes.id'))
    threshold = db.Column(db.Float)
    message = db.Column(db.String(200))
    destination = db.Column(db.String(100))
    
    def configureAlert(self, id, threshold, float):
        pass
    
    def sendAlert(self, message):
        pass
    
    def checkThreshold(self, data):
        return False
    
    def checkLogForAlerts(self, id, query):
        return False

class Report(db.Model):
    __tablename__ = 'reports'

    id = db.Column(db.Integer, primary_key=True)
    nodeId = db.Column(db.Integer, db.ForeignKey('nodes.id'))
    startDate = db.Column(db.DateTime)
    endDate = db.Column(db.DateTime)
    content = db.Column(db.Text)
    
    def generateReport(self, id, startDate, endDate):
        return Report
    
    def exportReport(self, reportId):
        pass

class WebDisplay(db.Model):
    __tablename__ = 'web_displays'

    id = db.Column(db.Integer, primary_key=True)
    nodeId = db.Column(db.Integer, db.ForeignKey('nodes.id'))
    frameUrlLogs = db.Column(db.String(500))
    frameUrlPerformance = db.Column(db.String(500))
    
    def generateIframeUrl(self, id, type):
        return ""
    
    def displayData(self, nodeId):
        pass

class ScriptGenerator(db.Model):
    __tablename__ = 'script_generators'

    id = db.Column(db.Integer, primary_key=True)
    nodeId = db.Column(db.Integer, db.ForeignKey('nodes.id'))
    typeScript = db.Column(db.Enum(TypeScript))
    scriptContent = db.Column(db.Text)
    
    def generateScript(self, id, port, ip, type):
        return ""
    
    def saveScript(self):
        pass

class ExternalSystem(db.Model):
    __tablename__ = 'external_systems'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50))
    apiKey = db.Column(db.String(200))
    
    def fetchIframeUrlFromGrafana(self, nodeId, id, type):
        return ""
    
    def fetchLogFromLoki(self, id, query, startTime=None, endTime=None):
        return []
    
    def sendTelegramMessage(self, message):
        pass
    
    def addTargetToGrafana(self, nodeId, ipAddress, port):
        return False