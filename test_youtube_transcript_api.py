from youtube_transcript_api import YouTubeTranscriptApi
import sys

def test_transcript(video_id):
    print(f"Testing transcript fetch for Video ID: {video_id}")
    try:
        # 1. List available transcripts
        print("-" * 50)
        print("1. Listing available transcripts...")
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        for transcript in transcript_list:
            print(f"  - Language: {transcript.language} ({transcript.language_code})")
            print(f"    Generated: {transcript.is_generated}")
            print(f"    Translatable: {transcript.is_translatable}")
            
        # 2. Try to fetch Korean or English transcript
        print("-" * 50)
        print("2. Fetching transcript (trying 'ko' then 'en')...")
        
        try:
            transcript = transcript_list.find_transcript(['ko', 'en']) 
            print(f"  -> Found transcript in language: {transcript.language_code}")
        except:
            print("  -> specific language not found, trying generated...")
            transcript = transcript_list.find_generated_transcript(['ko', 'en'])
            print(f"  -> Found generated transcript: {transcript.language_code}")

        # 3. Print first 5 lines
        print("-" * 50)
        print("3. Transcript Content (First 5 lines):")
        entries = transcript.fetch()
        for i, entry in enumerate(entries[:5]):
            print(f"  [{i+1}] {entry['text']}")
            
        print("-" * 50)
        print("SUCCESS: Transcript fetched successfully.")
        
    except Exception as e:
        print("-" * 50)
        print(f"ERROR: Failed to fetch transcript.")
        print(f"Error details: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Default video ID (YouTube Rewind 2018 or any video with captions)
    # The user's video: byiF4GoJ9gA 
    video_id = "byiF4GoJ9gA" 
    
    if len(sys.argv) > 1:
        video_id = sys.argv[1]
        
    test_transcript(video_id)
