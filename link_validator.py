import re
from typing import Tuple

class LinkValidator:
    """Validates links for different platforms and service types"""
    
    # Platform patterns
    PATTERNS = {
        'youtube_channel': [
            r'(?:https?://)?(?:www\.)?youtube\.com/@[\w-]+',
            r'(?:https?://)?(?:www\.)?youtube\.com/channel/[\w-]+',
            r'(?:https?://)?(?:www\.)?youtube\.com/c/[\w-]+',
            r'(?:https?://)?(?:www\.)?youtube\.com/user/[\w-]+'
        ],
        'youtube_video': [
            r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=[\w-]+',
            r'(?:https?://)?youtu\.be/[\w-]+'
        ],
        'youtube_shorts': [
            r'(?:https?://)?(?:www\.)?youtube\.com/shorts/[\w-]+'
        ],
        'instagram_profile': [
            r'(?:https?://)?(?:www\.)?instagram\.com/[\w.]+/?$'
        ],
        'instagram_post': [
            r'(?:https?://)?(?:www\.)?instagram\.com/p/[\w-]+',
            r'(?:https?://)?(?:www\.)?instagram\.com/reel/[\w-]+'
        ],
        'tiktok_profile': [
            r'(?:https?://)?(?:www\.)?tiktok\.com/@[\w.]+'
        ],
        'tiktok_video': [
            r'(?:https?://)?(?:www\.)?tiktok\.com/@[\w.]+/video/\d+'
        ],
        'facebook_profile': [
            r'(?:https?://)?(?:www\.)?facebook\.com/[\w.]+'
        ],
        'facebook_page': [
            r'(?:https?://)?(?:www\.)?facebook\.com/pages/[\w-]+/\d+'
        ],
        'twitter_profile': [
            r'(?:https?://)?(?:www\.)?(?:twitter|x)\.com/[\w]+/?$'
        ],
        'twitter_tweet': [
            r'(?:https?://)?(?:www\.)?(?:twitter|x)\.com/[\w]+/status/\d+'
        ],
        'telegram': [
            r'(?:https?://)?t\.me/[\w]+'
        ],
        'twitch': [
            r'(?:https?://)?(?:www\.)?twitch\.tv/[\w]+'
        ],
        'kick': [
            r'(?:https?://)?(?:www\.)?kick\.com/[\w]+'
        ],
        'snapchat': [
            r'(?:https?://)?(?:www\.)?snapchat\.com/add/[\w.]+'
        ],
        'threads': [
            r'(?:https?://)?(?:www\.)?threads\.net/@[\w.]+'
        ],
        'reddit_profile': [
            r'(?:https?://)?(?:www\.)?reddit\.com/user/[\w-]+'
        ],
        'reddit_post': [
            r'(?:https?://)?(?:www\.)?reddit\.com/r/[\w]+/comments/[\w]+/'
        ],
        'linkedin_profile': [
            r'(?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+'
        ],
        'linkedin_company': [
            r'(?:https?://)?(?:www\.)?linkedin\.com/company/[\w-]+'
        ],
        'spotify_artist': [
            r'(?:https?://)?open\.spotify\.com/artist/[\w]+'
        ],
        'spotify_track': [
            r'(?:https?://)?open\.spotify\.com/track/[\w]+'
        ],
        'spotify_playlist': [
            r'(?:https?://)?open\.spotify\.com/playlist/[\w]+'
        ],
        'generic_url': [
            r'(?:https?://)?(?:www\.)?[\w.-]+\.[\w]{2,}(?:/[\w.-]*)*'
        ]
    }
    
    @staticmethod
    def detect_link_type(link: str, platform: str, service_type: str) -> Tuple[bool, str]:
        """
        Validate link based on platform and service type
        Returns: (is_valid, message)
        """
        link = link.strip()
        
        # YouTube validation
        if platform == 'youtube':
            if service_type in ['subscribers', 'subscriber']:
                # Must be channel link
                for pattern in LinkValidator.PATTERNS['youtube_channel']:
                    if re.match(pattern, link, re.IGNORECASE):
                        return True, "Valid YouTube channel link"
                return False, "❌ Invalid link. YouTube Subscribers require a channel link (youtube.com/@username or /channel/ID)"
            
            elif service_type in ['views', 'view', 'likes', 'like', 'comments', 'comment']:
                # Must be video link
                for pattern in LinkValidator.PATTERNS['youtube_video']:
                    if re.match(pattern, link, re.IGNORECASE):
                        return True, "Valid YouTube video link"
                return False, "❌ Invalid link. YouTube Views/Likes require a video link (youtube.com/watch?v=...)"
            
            elif 'shorts' in service_type.lower():
                # Must be shorts link
                for pattern in LinkValidator.PATTERNS['youtube_shorts']:
                    if re.match(pattern, link, re.IGNORECASE):
                        return True, "Valid YouTube Shorts link"
                return False, "❌ Invalid link. YouTube Shorts require a shorts link (youtube.com/shorts/...)"
            
            elif 'live' in service_type.lower():
                # Can be video or channel
                for pattern in LinkValidator.PATTERNS['youtube_video'] + LinkValidator.PATTERNS['youtube_channel']:
                    if re.match(pattern, link, re.IGNORECASE):
                        return True, "Valid YouTube link"
                return False, "❌ Invalid link. Provide a YouTube video or channel link"
        
        # Instagram validation
        elif platform == 'instagram':
            if service_type in ['followers', 'follower']:
                for pattern in LinkValidator.PATTERNS['instagram_profile']:
                    if re.match(pattern, link, re.IGNORECASE):
                        return True, "Valid Instagram profile link"
                return False, "❌ Invalid link. Instagram Followers require a profile link (instagram.com/username)"
            
            elif service_type in ['likes', 'like', 'views', 'view', 'comments', 'comment']:
                for pattern in LinkValidator.PATTERNS['instagram_post']:
                    if re.match(pattern, link, re.IGNORECASE):
                        return True, "Valid Instagram post/reel link"
                return False, "❌ Invalid link. Provide an Instagram post or reel link (instagram.com/p/... or /reel/...)"
        
        # TikTok validation
        elif platform == 'tiktok':
            if service_type in ['followers', 'follower']:
                for pattern in LinkValidator.PATTERNS['tiktok_profile']:
                    if re.match(pattern, link, re.IGNORECASE):
                        return True, "Valid TikTok profile link"
                return False, "❌ Invalid link. TikTok Followers require a profile link (tiktok.com/@username)"
            
            elif service_type in ['likes', 'like', 'views', 'view', 'comments', 'comment']:
                for pattern in LinkValidator.PATTERNS['tiktok_video']:
                    if re.match(pattern, link, re.IGNORECASE):
                        return True, "Valid TikTok video link"
                # Also accept profile link for some services
                for pattern in LinkValidator.PATTERNS['tiktok_profile']:
                    if re.match(pattern, link, re.IGNORECASE):
                        return True, "Valid TikTok link"
                return False, "❌ Invalid link. Provide a TikTok video link (tiktok.com/@user/video/...)"
        
        # Twitter/X validation
        elif platform in ['twitter', 'x']:
            if service_type in ['followers', 'follower']:
                for pattern in LinkValidator.PATTERNS['twitter_profile']:
                    if re.match(pattern, link, re.IGNORECASE):
                        return True, "Valid Twitter/X profile link"
                return False, "❌ Invalid link. Twitter Followers require a profile link (twitter.com/username or x.com/username)"
            
            elif service_type in ['likes', 'like', 'retweets', 'retweet', 'views', 'view']:
                for pattern in LinkValidator.PATTERNS['twitter_tweet']:
                    if re.match(pattern, link, re.IGNORECASE):
                        return True, "Valid Twitter/X tweet link"
                return False, "❌ Invalid link. Provide a tweet link (twitter.com/user/status/...)"
        
        # Facebook validation
        elif platform == 'facebook':
            for pattern in LinkValidator.PATTERNS['facebook_profile'] + LinkValidator.PATTERNS['facebook_page']:
                if re.match(pattern, link, re.IGNORECASE):
                    return True, "Valid Facebook link"
            return False, "❌ Invalid link. Provide a Facebook profile or page link"
        
        # Telegram validation
        elif platform == 'telegram':
            for pattern in LinkValidator.PATTERNS['telegram']:
                if re.match(pattern, link, re.IGNORECASE):
                    return True, "Valid Telegram link"
            return False, "❌ Invalid link. Provide a Telegram link (t.me/username)"
        
        # Twitch validation
        elif platform == 'twitch':
            for pattern in LinkValidator.PATTERNS['twitch']:
                if re.match(pattern, link, re.IGNORECASE):
                    return True, "Valid Twitch link"
            return False, "❌ Invalid link. Provide a Twitch channel link (twitch.tv/username)"
        
        # Kick validation
        elif platform == 'kick':
            for pattern in LinkValidator.PATTERNS['kick']:
                if re.match(pattern, link, re.IGNORECASE):
                    return True, "Valid Kick link"
            return False, "❌ Invalid link. Provide a Kick channel link (kick.com/username)"
        
        # Snapchat validation
        elif platform == 'snapchat':
            for pattern in LinkValidator.PATTERNS['snapchat']:
                if re.match(pattern, link, re.IGNORECASE):
                    return True, "Valid Snapchat link"
            return False, "❌ Invalid link. Provide a Snapchat profile link (snapchat.com/add/username)"
        
        # Threads validation
        elif platform == 'threads':
            for pattern in LinkValidator.PATTERNS['threads']:
                if re.match(pattern, link, re.IGNORECASE):
                    return True, "Valid Threads link"
            return False, "❌ Invalid link. Provide a Threads profile link (threads.net/@username)"
        
        # Reddit validation
        elif platform == 'reddit':
            if service_type in ['followers', 'follower', 'karma']:
                for pattern in LinkValidator.PATTERNS['reddit_profile']:
                    if re.match(pattern, link, re.IGNORECASE):
                        return True, "Valid Reddit profile link"
                return False, "❌ Invalid link. Provide a Reddit profile link (reddit.com/user/username)"
            else:
                for pattern in LinkValidator.PATTERNS['reddit_post']:
                    if re.match(pattern, link, re.IGNORECASE):
                        return True, "Valid Reddit post link"
                return False, "❌ Invalid link. Provide a Reddit post link"
        
        # LinkedIn validation
        elif platform == 'linkedin':
            for pattern in LinkValidator.PATTERNS['linkedin_profile'] + LinkValidator.PATTERNS['linkedin_company']:
                if re.match(pattern, link, re.IGNORECASE):
                    return True, "Valid LinkedIn link"
            return False, "❌ Invalid link. Provide a LinkedIn profile or company link"
        
        # Spotify validation
        elif platform == 'spotify':
            for pattern in (LinkValidator.PATTERNS['spotify_artist'] + 
                          LinkValidator.PATTERNS['spotify_track'] + 
                          LinkValidator.PATTERNS['spotify_playlist']):
                if re.match(pattern, link, re.IGNORECASE):
                    return True, "Valid Spotify link"
            return False, "❌ Invalid link. Provide a Spotify artist, track, or playlist link"
        
        # Generic URL validation for other platforms
        else:
            for pattern in LinkValidator.PATTERNS['generic_url']:
                if re.match(pattern, link, re.IGNORECASE):
                    return True, "Valid URL"
            return False, "❌ Invalid URL format"
