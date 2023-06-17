import argparse
from time import sleep
from selenium import webdriver
from datetime import date, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


class MeckanoReporter():
    def __init__(self, username, password, verbose=False):
        self.driver = webdriver.Firefox()
        self.username = username
        self.password = password
        self.verbose = verbose

        self.main_page   = "https://app.meckano.co.il/login.php#login"
        self.report_page = "https://app.meckano.co.il/#report"

    def __del__(self):
        """ destructor """
        self.driver.close()

    def __login(self):
        """ log in to the site """
        self.driver.get(self.main_page)

        element = self.driver.find_element(By.ID, "loginForm")
        element.find_element(By.ID, "email").send_keys(self.username)
        element.find_element(By.ID, "password").send_keys(self.password)
        sleep(1)
        element.find_element(By.NAME, "submit").click()

    def __go_to_report(self, starting_date, ending_date):
        """ go to the report hours page """
        self.driver.find_element(By.CLASS_NAME, "calender").click()

        if starting_date is not None and ending_date is not None:
            self.driver.get(f"{self.report_page}/{starting_date}/{ending_date}")

        sleep(1)

    def __find_report_hours(self, base_element, index, _time, clear_page=False):
        """ find and set the hour input section """
        input_entries = base_element.find_elements(By.CLASS_NAME, "report-entry")
        span_entries  = base_element.find_elements(By.CLASS_NAME, "ltr")

        if len(span_entries) != 2 and self.verbose:
            print(f"there are more or less then 2 entries in {span_entries}")
        else:
            span_entries[index].click()

            if not clear_page:
                input_entries[index].send_keys(_time)
            else:
                input_entries[index].send_keys(Keys.DELETE)

    def __report_hours(self, start_hour, end_hour, refresh_page_function, accept_date_list=None, ignore_date_list=[], clear_page=False, override=False):
        """ find and set all the hours input section to the start and end hours """

        def move_to_next_line(move_window, height, line_index):
            line_index += 1
            return move_to_next_item(move_window, height), line_index

        def move_to_next_item(move_window, height):
            move_window(f"window.scrollTo(0, {height})")
            height += height_addition
            return height

        report_table = self.driver.find_element(By.CLASS_NAME, "employee-report")
        report_table_lines = report_table.find_elements(By.TAG_NAME, "tr")

        line_index = 0
        max_line_index = len(report_table_lines)
        entry_index = 0

        height = 50
        height_addition = 30

        while line_index != max_line_index:
            report_line = report_table_lines[line_index]
            class_name = report_line.get_attribute("class")

            if "no-pointer" in class_name or "highlightingRestDays" in class_name:
                if self.verbose:
                    print("rest day -> passing")

                height, line_index = move_to_next_line(self.driver.execute_script, height, line_index)
                continue

            report_line_info = report_line.find_element(By.CLASS_NAME, "employee-information")
            date_info = report_line_info.find_element(By.TAG_NAME, "p").text
            special_date_info = report_line.find_element(By.CLASS_NAME, "specialDayDescription").text
            employee_special_date_info = report_line.find_element(By.CLASS_NAME, "missing").text
            special_reason = report_line.find_element(By.CLASS_NAME, "text-center").find_element(By.CLASS_NAME, "missing").text
            checkin = report_line.find_element(By.CLASS_NAME, "checkin").text
            checkout = report_line.find_element(By.CLASS_NAME, "checkout").text

            if self.verbose:
                print("-" * 20)
                print(date_info)

            if (special_reason    != "" and special_reason    != "         " and special_reason    != "+") or \
               (special_date_info != "" and special_date_info != "         " and special_date_info != "+") or \
               (employee_special_date_info != "+" and employee_special_date_info != "         ") or \
               (not override and (checkin  != "" and checkin  != "         " and checkin   != "                  " and \
                                  checkout != "" and checkout != "         " and checkout  != "                  ")):
                if self.verbose:
                    print(f"special reason - passing -> !{special_reason}!")
                    print(f"employee special day - passing -> !{employee_special_date_info}!")
                    print(f"special day - passing -> !{special_date_info}!")
                    print(f"date already field - passing -> !{checkin}! - !{checkout}!")

                height, line_index = move_to_next_line(self.driver.execute_script, height, line_index)
                continue

            if date_info.split(" ")[0] in ignore_date_list:
                height, line_index = move_to_next_line(self.driver.execute_script, height, line_index)
                continue

            if accept_date_list is None or date_info.split(" ")[0] in accept_date_list:
                _time = start_hour if entry_index == 0 else end_hour
                self.__find_report_hours(report_line, entry_index, _time, clear_page)
            else:
                height, line_index = move_to_next_line(self.driver.execute_script, height, line_index)
                continue

            entry_index += 1

            if entry_index == 2:
                line_index += 1
                entry_index = 0

            refresh_page_function()

            height = move_to_next_item(self.driver.execute_script, height)
            report_table = self.driver.find_element(By.CLASS_NAME, "employee-report")
            report_table_lines = report_table.find_elements(By.TAG_NAME, "tr")

    def __report_a_day(self, day_date, start_hour="09:00", end_hour="19:00", clear_page=False, override=False):
        """ report one day only """
        _date = f"{day_date.day}/{day_date.month}/{day_date.year}"

        self.report(start_hour=start_hour, end_hour=end_hour, accept_date_list=[_date], clear_page=clear_page, override=override)

    def __report_a_week(self, start_week_day, start_hour="09:00", end_hour="19:00", clear_page=False, override=False):
        """ report a week starting from the last Sunday """
        end_week_day = start_week_day + timedelta(days=6)
        format_number_date = lambda number: f"{number}" if int(number) >= 10 else f"0{number}"

        week_days = []
        for i in range(7):
            current_week_day = start_week_day + timedelta(days=i)

            if current_week_day > end_week_day:
                break

            week_days.append(f"{format_number_date(current_week_day.day)}/{format_number_date(current_week_day.month)}/{current_week_day.year}")

        self.report(start_hour=start_hour, end_hour=end_hour, accept_date_list=week_days, clear_page=clear_page, override=override)

    def report(self, starting_date=None, ending_date=None, start_hour="09:00", end_hour="19:00", accept_date_list=None, ignore_date_list=[], clear_page=False, override=False):
        self.__login()
        sleep(3)

        refresh_page = lambda: self.__go_to_report(starting_date, ending_date)
        refresh_page()

        self.__report_hours(start_hour, end_hour, refresh_page, accept_date_list, ignore_date_list, clear_page, override=override)

    def report_today(self, start_hour="09:00", end_hour="19:00", clear_page=False, override=False):
        self.__report_a_day(day_date=date.today(), start_hour=start_hour, end_hour=end_hour, clear_page=clear_page, override=override)

    def report_yesterday(self, start_hour="09:00", end_hour="19:00", clear_page=False, override=False):
        yesterday = date.today() - timedelta(days=1)
        self.__report_a_day(day_date=yesterday, start_hour=start_hour, end_hour=end_hour, clear_page=clear_page, override=override)

    def report_last_week(self, start_hour="09:00", end_hour="19:00", clear_page=False, override=False):
        _date = date.today() - timedelta(days=7)

        for i in range(7):
            future_date = _date + timedelta(days=i)
            if future_date.ctime().startswith("Sun"):
                self.__report_a_week(start_week_day=future_date, start_hour=start_hour, end_hour=end_hour, clear_page=clear_page, override=override)
                return


def cli_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('username',      type=str,  help='username / email for the meckano website')
    parser.add_argument('password',      type=str,  help='password for the meckano website')
    parser.add_argument('--system_mode', type=str,  help='the action to activate', choices=["report_today", "report_yesterday", "report_last_week", "report"], default="report")
    parser.add_argument('--start_date',  type=str,  help='the date to start the hour report')
    parser.add_argument('--end_date',    type=str,  help='the date to end the hour report')
    parser.add_argument('--start_time',  type=str,  help='the time to set at the start of each day', default="09:00")
    parser.add_argument('--end_time',    type=str,  help='the time to set at the end of each day', default="19:00")
    parser.add_argument('--clear_page',  type=bool, help='clear all dates', default=False)
    parser.add_argument('--override_existing',  type=bool, help='override existing time', default=False)
    parser.add_argument('--verbose',     type=bool, help='set erporter to verbose mode', default=False)
    # parser.add_argument('--ignore_date_list', type=list, help='dates to not report', default=[])
    # parser.add_argument('--accept_date_list', type=list, help='dates to report', default=[])

    args = parser.parse_args()

    reporter = MeckanoReporter(args.username, args.password, verbose=args.verbose)

    if args.system_mode == "report":
        reporter.report(args.start_date, args.end_date, args.start_time, args.end_time, args.clear_page, override=args.override_existing)
    elif args.system_mode == "report_today":
        reporter.report_today(args.start_time, args.end_time, args.clear_page, override=args.override_existing)
    elif args.system_mode == "report_yesterday":
        reporter.report_yesterday(args.start_time, args.end_time, args.clear_page, override=args.override_existing)
    elif args.system_mode == "report_last_week":
        reporter.report_last_week(args.start_time, args.end_time, args.clear_page, override=args.override_existing)
    else:
        print(f"There is no system mode '{args.system_mode}'")


if __name__ == '__main__':
    cli_arguments()
