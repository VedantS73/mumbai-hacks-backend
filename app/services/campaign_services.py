from app.models.user import User
from app.models.campaign import Campaign
from sqlalchemy import and_

class CampaignService:
    @staticmethod
    def get_matching_users_count(campaign):
        query = User.query.filter(
            and_(
                User.age >= campaign.lower_age,
                User.age <= campaign.upper_age,
                User.gender == campaign.gender
            )
        )
        
        if campaign.location:
            query = query.filter(User.location.in_(campaign.location))
            
        if campaign.occupation:
            query = query.filter(User.occupation.in_(campaign.occupation))
            
        return query.count()
    
    @staticmethod
    def get_campaign_by_id(campaign_id):
        return Campaign.query.get(campaign_id)