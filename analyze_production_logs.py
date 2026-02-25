import json
import sys

def analyze_logs(file_path):
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        errors = []
        timeout_likely = []
        for entry in data:
            msg = entry.get('message', '')
            attributes = entry.get('attributes', {})
            level = attributes.get('level', '')
            
            # Look for errors or timeouts
            if 'timeout' in msg.lower() or 'timed out' in msg.lower() or 'exception' in msg.lower() or 'failed' in msg.lower() or level == 'error':
                errors.append(entry)
            
            # Look for long gaps or unfinished sessions?
            # For now just collect obvious errors
            
        print(f"Total entries: {len(data)}")
        print(f"Error-level or matching-message entries: {len(errors)}")
        
        # Group by message to see most common issues
        from collections import Counter
        msg_counts = Counter(e.get('message', '') for e in errors)
        print("\nCommon Error Messages:")
        for msg, count in msg_counts.most_common(20):
            print(f"[{count}] {msg[:100]}...")
            
        # Specific search for "timed out"
        timeouts = [i for i, e in enumerate(data) if 'timed out' in e.get('message', '').lower()]
        print(f"\nSpecific 'timed out' entries: {len(timeouts)}")
        # Find log_ids for timeouts
        print("\nSessions with timeouts:")
        target_log_id = None
        for i in timeouts:
            e = data[i]
            # Look back for log_id
            log_id = "Unknown"
            replica = e.get('tags', {}).get('replica')
            for j in range(i-1, -1, -1):
                prev = data[j]
                if prev.get('tags', {}).get('replica') == replica:
                    msg = prev.get('message', '')
                    if 'log ' in msg:
                        import re
                        match = re.search(r'log ([a-f0-9\-]+)', msg)
                        if match:
                            log_id = match.group(1)
                            target_log_id = log_id
                            break
            print(f"  Timeout at {e.get('timestamp')} - Log ID: {log_id}")

        if target_log_id:
            print(f"\n--- Detailed Trace for Log ID: {target_log_id} ---")
            start_idx = 0
            for i, e in enumerate(data):
                if target_log_id in e.get('message', ''):
                    start_idx = i
                    break
            
            replica = data[start_idx].get('tags', {}).get('replica')
            for i in range(start_idx, len(data)):
                e = data[i]
                if e.get('tags', {}).get('replica') == replica:
                    msg = e.get('message', '')
                    if 'Gemini contents:' in msg:
                        print(f"\nPROMPT FOUND at {e.get('timestamp')}:")
                        print(msg)
                    if 'Agent received' in msg:
                        pass
                    elif i > start_idx + 400: break
                    else:
                        if target_log_id in msg or 'Gemini' in msg:
                           print(f"    {e.get('timestamp')} {msg}")
                if 'timed out after 120s' in e.get('message', ''):
                    print(f"    {e.get('timestamp')} {e.get('message')}")
                    break

        print("\n--- Global Network/HTTP Errors ---")
        network_errors = [e for e in data if any(word in e.get('message', '').lower() for word in ['connectionerror', 'readtimeout', 'connecttimeout', 'remoteprotocolerror', 'network error', 'connection reset'])]
        print(f"Found {len(network_errors)} potential network errors")
        for e in network_errors[:20]:
            print(f"  {e.get('timestamp')} {e.get('message')}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    analyze_logs('/home/fabian/dev/work/snapandsay/logs.1771605223172.json')
