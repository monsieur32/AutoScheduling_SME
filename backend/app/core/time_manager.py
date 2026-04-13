"""
Time Manager to handle working hours, shifts, breaks, and overtime logic.
Converts linear processing time to real-world clock time considering off-hours.
All times are represented as integer minutes starting from Day 0, 07:00 AM (t=0).
"""

from typing import Dict, Any, Optional

DAY_MINUTES = 1440

class ShiftManager:
    def __init__(self, overtime_config: Optional[Dict[str, Any]] = None):
        """
        overtime_config example: {"enabled": True, "end_time_mins": 630} # e.g. 17:30 (10.5 hrs from 7AM)
        """
        self.shift_start = 30  # 07:30
        self.lunch_start = 265  # 11:25
        self.lunch_end = 310    # 12:10
        self.shift_end = 510    # 15:30
        
        self.has_overtime = False
        self.overtime_end = self.shift_end
        
        if overtime_config and overtime_config.get("enabled"):
            # Assume end_time_mins is relative to 07:00. e.g. 17:30 is 10.5 hours = 630 mins
            # Or if it's passed as actual hour, we will standardise it to minutes from 07:00
            end_val = overtime_config.get("end_time_mins", 510)
            if end_val > self.shift_end:
                self.has_overtime = True
                self.overtime_end = end_val

    def get_next_working_time(self, t: int) -> int:
        """
        If current time t is inside a break or off-hours, advance to the start of the next working block.
        """
        day = t // DAY_MINUTES
        minute_in_day = t % DAY_MINUTES
        
        # Before shift starts (07:00 - 07:30)
        if minute_in_day < self.shift_start:
            return day * DAY_MINUTES + self.shift_start
            
        # During lunch break (11:25 - 12:10)
        if self.lunch_start <= minute_in_day < self.lunch_end:
            return day * DAY_MINUTES + self.lunch_end
            
        # After shift ends (or overtime ends)
        effective_end = self.overtime_end if self.has_overtime else self.shift_end
        if minute_in_day >= effective_end:
            # Advance to next day's shift start
            return (day + 1) * DAY_MINUTES + self.shift_start
            
        return t

    def add_working_time(self, start_t: int, duration: int) -> int:
        """
        Adds `duration` working minutes to `start_t`.
        Any time overlapping with breaks or off-hours does not consume `duration`.
        """
        current_t = self.get_next_working_time(start_t)
        remaining = duration

        while remaining > 0:
            day = current_t // DAY_MINUTES
            minute_in_day = current_t % DAY_MINUTES

            effective_end = self.overtime_end if self.has_overtime else self.shift_end

            # Determine the end of the current continuous working block
            if minute_in_day < self.shift_start:
                # Before shift starts (e.g. t exactly on day boundary)
                # get_next_working_time should have handled this, but safety net:
                current_t = day * DAY_MINUTES + self.shift_start
                continue
            elif minute_in_day < self.lunch_start:
                # Morning block: shift_start → lunch_start
                block_end_t = day * DAY_MINUTES + self.lunch_start
            elif minute_in_day < self.lunch_end:
                # Inside lunch break (safety net — get_next_working_time should skip this)
                current_t = day * DAY_MINUTES + self.lunch_end
                continue
            else:
                # Afternoon block: lunch_end → effective_end
                block_end_t = day * DAY_MINUTES + effective_end

            available_mins = block_end_t - current_t

            if remaining <= available_mins:
                current_t += remaining
                remaining = 0
            else:
                remaining -= available_mins
                current_t = block_end_t
                current_t = self.get_next_working_time(current_t)

        return current_t
