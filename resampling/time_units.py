import datetime

def seconds_to_unix_time(seconds_since_1978):
    # Add seconds since 1978-01-01 00:00:00 to the base datetime
    base_datetime = datetime.datetime(1978, 1, 1, 0, 0, 0)
    target_datetime = base_datetime + datetime.timedelta(seconds=seconds_since_1978)
    
    # Convert the datetime object to Unix timestamp
    unix_timestamp = target_datetime.timestamp()
    
    return unix_timestamp

# Example usage:
#seconds_since_1978 = 1234567890  # Example value
#unix_time = seconds_to_unix_time(seconds_since_1978)
#print(unix_time)

