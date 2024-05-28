import unittest
from datetime import datetime, date
from biologic_tracker import get_previous_weekday, distribute_volume,get_working_days,find_available_days

class TestGetPreviousWeekday(unittest.TestCase):
    def test_monday(self):
        self.assertEqual(get_previous_weekday(date(2024, 5, 6)), date(2024, 5, 3))  # Monday to previous Friday

    def test_tuesday(self):
        self.assertEqual(get_previous_weekday(date(2024, 5, 7)), date(2024, 5, 3))  # Tuesday to previous Friday

    def test_wednesday(self):
        self.assertEqual(get_previous_weekday(date(2024, 5, 8)), date(2024, 5, 6))  # Wednesday to previous Monday

    def test_thursday(self):
        self.assertEqual(get_previous_weekday(date(2024, 5, 9)), date(2024, 5, 7))  # Thursday to previous Tuesday

    def test_friday(self):
        self.assertEqual(get_previous_weekday(date(2024, 5, 10)), date(2024, 5, 8))  # Friday to previous Wednesday

    def test_saturday(self):
        self.assertEqual(get_previous_weekday(date(2024, 5, 11)), date(2024, 5, 9))  # Saturday to previous Thursday

    def test_sunday(self):
        self.assertEqual(get_previous_weekday(date(2024, 5, 12)), date(2024, 5, 10))  # Sunday to previous Friday

class test_distribute_volume(unittest.TestCase):
    def test_no_changes(self):
        self.assertEqual(distribute_volume("prepA",100),[("prepA",100)])
    def test_change_volumes(self):
        self.assertEqual(distribute_volume("prepA",1300),[("prepA",500),("prepA",500),("prepA",300)])

class TestGetWorkingDays(unittest.TestCase):
    def test_entire_week(self):
        self.assertEqual(
            get_working_days(date(2023, 5, 22), date(2023, 5, 28)),
            [date(2023, 5, 22), date(2023, 5, 23), date(2023, 5, 24), date(2023, 5, 25), date(2023, 5, 26)]
        )  # Monday to Sunday, should return Monday to Friday

    def test_single_day(self):
        self.assertEqual(
            get_working_days(date(2023, 5, 22), date(2023, 5, 22)),
            [date(2023, 5, 22)]
        )  # Single Monday

    def test_weekend(self):
        self.assertEqual(
            get_working_days(date(2023, 5, 27), date(2023, 5, 28)),
            []
        )  # Saturday to Sunday, no working days

    def test_mixed_days(self):
        self.assertEqual(
            get_working_days(date(2023, 5, 25), date(2023, 5, 29)),
            [date(2023, 5, 25), date(2023, 5, 26), date(2023, 5, 29)]
        )  # Thursday to Monday, should return Thursday, Friday, Monday

    def test_start_date_after_end_date(self):
        self.assertEqual(
            get_working_days(date(2023, 5, 28), date(2023, 5, 22)),
            []
        )  # Start date after end date, should return empty list

class TestFindAvailableDays(unittest.TestCase):
    """ 
    Test cases
    1. D1[] D2[] D3[]     | M -> all open
    2. D1[M] D2[M] D3[]   | M -> all open
    3. D1[M,M] D2[B] D3[] | M -> D3 open
    4. D1[M] D2[B] D3[]   | M -> D1 and D3 open
    5. D1[M] D2[B] D3[]   | B -> D2 and D3 open
    6. D1[M,M] D2[B,B] D3[M,M] | M -> None open
    """
    
    
    def test_one(self):
        date_list = [date(2023, 5, 22), date(2023, 5, 23), date(2023, 5, 24)]
        prep_details = {'prepM1': {'type': 'media'}, 'prepM2': {'type': 'media'},
                        'prepB1': {'type': 'buffer'}, 'prepB2': {'type': 'buffer'}}
        schedule = {}
        self.assertEqual(
            find_available_days(schedule, 'media', date_list, prep_details),
            [date(2023, 5, 22), date(2023, 5, 23), date(2023, 5, 24)]
        )

    def test_two(self):
        date_list = [date(2023, 5, 22), date(2023, 5, 23), date(2023, 5, 24)]
        prep_details = {'prepM1': {'type': 'media'}, 'prepM2': {'type': 'media'},
                        'prepB1': {'type': 'buffer'}, 'prepB2': {'type': 'buffer'}}
        schedule = {
            date(2023, 5, 22): [('prepM1', 100)],
            date(2023, 5, 23): [('prepM2', 200)]
        }
        self.assertEqual(
            find_available_days(schedule, 'media', date_list, prep_details),
            [date(2023, 5, 22), date(2023, 5, 23), date(2023, 5, 24)]
        )

    def test_three(self):
        date_list = [date(2023, 5, 22), date(2023, 5, 23), date(2023, 5, 24)]
        prep_details = {'prepM1': {'type': 'media'}, 'prepM2': {'type': 'media'},
                        'prepB1': {'type': 'buffer'}, 'prepB2': {'type': 'buffer'}}
        schedule = {
            date(2023, 5, 22): [('prepM1', 100), ('prepM2', 150)],
            date(2023, 5, 23): [('prepB1', 200)]
        }
        
        self.assertEqual(
            find_available_days(schedule, 'media', date_list, prep_details),
            [date(2023, 5, 24)]
        )

    def test_four(self):
        date_list = [date(2023, 5, 22), date(2023, 5, 23), date(2023, 5, 24)]
        prep_details = {'prepM1': {'type': 'media'}, 'prepM2': {'type': 'media'},
                        'prepB1': {'type': 'buffer'}, 'prepB2': {'type': 'buffer'}}
        schedule = {
            date(2023, 5, 22): [('prepM1', 100)],
            date(2023, 5, 23): [('prepB1', 200)]
        }

        self.assertEqual(
            find_available_days(schedule, 'media', date_list, prep_details),
            [date(2023, 5, 22),date(2023, 5, 24)]
        )

    def test_five(self):
        date_list = [date(2023, 5, 22), date(2023, 5, 23), date(2023, 5, 24)]
        prep_details = {'prepM1': {'type': 'media'}, 'prepM2': {'type': 'media'},
                        'prepB1': {'type': 'buffer'}, 'prepB2': {'type': 'buffer'}}
        schedule = {
            date(2023, 5, 22): [('prepM1', 100)],
            date(2023, 5, 23): [('prepB1', 200)]
        }

        self.assertEqual(
            find_available_days(schedule, 'buffer', date_list, prep_details),
            [date(2023, 5, 23), date(2023, 5, 24)]
        )

    def test_six(self):
        date_list = [date(2023, 5, 22), date(2023, 5, 23), date(2023, 5, 24)]
        prep_details = {'prepM1': {'type': 'media'}, 'prepM2': {'type': 'media'},
                        'prepB1': {'type': 'buffer'}, 'prepB2': {'type': 'buffer'}}
        schedule = {
            date(2023, 5, 22): [('prepM1', 100),('prepM2', 100)],
            date(2023, 5, 23): [('prepB1', 200),('prepB2', 200)],
            date(2023, 5, 24): [('prepM1', 100),('prepM2', 100)],
        }

        self.assertEqual(
            find_available_days(schedule, 'buffer', date_list, prep_details),
            []
        )
if __name__ == '__main__':
    unittest.main()