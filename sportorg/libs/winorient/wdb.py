def get_wdb_encoding():
    """
    Get standard encoding, used in WinOrient files - Windows-1251 (Cyrillic)
    :return:
    """
    return 'windows-1251'


def get_wdb_byteorder():
    """
    Get standard byteorder for WinOrient files, on Windows it's little-endian.
    :return:
    """
    return 'little'


def format_string_to_bytes(string, length):
    """
    Format string into byte array, according to length of target array.
    If necessary, fill the gap between last string char and the end of array with \0
    :param string:
    :param length:
    :return:
    """
    if string is None:
        string = ''
    ret = bytearray(string, get_wdb_encoding())
    if len(string) > length:
        return ret[0:length]
    for i in range(len(string), length):
        ret.append(0)  # 32=space
    return ret


def encode(byte_array):
    """
    Get string from byte array. Note, that \0 is a line end char.
    e.g. b'\xc4\xeb\xe8\xed\xed\xe0\xff 2\x00\x00\x00' -> b'\xc4\xeb\xe8\xed\xed\xe0\xff 2' -> 'Длинная 2'
    :param byte_array:
    :return:
    """
    obj = byte_array
    null_index = obj.find(0x00)
    if null_index > -1:
        obj = obj[0:null_index]
    return str(obj, get_wdb_encoding())


def bytes_compare(obj1, obj2):
    """
    Compare 2 objects byte-2-byte. Will be removed in release version =)
    :param obj1:
    :param obj2:
    """

    # turn on / off debug
    release = 1

    if release == 1:
        return False

    if len(obj1) != len(obj2):
        print('COMPARE: different length: %d and %d' % (len(obj1), len(obj2)))

    if str(bytearray(obj1)) != str(bytearray(obj2)):
        print('COMPARE: different strings')
        print(str(bytearray(obj1)))
        print(str(bytearray(obj2)))
        for i in range(len(obj1)):
            if bytearray(obj1)[i] != bytearray(obj2)[i]:
                print(i)
        return True
    return False


class WDBPunch:
    """
    Class, describing 1 punch - code and time.
    Used for start, finish, check, clear and control point.
    """

    def __init__(self, code=0, time=0):
        self.code = code  # number 0-255
        self.time = time  # seconds * 100, e.g. 01:01:01 = 366100

    def parse_bytes(self, byte_array):
        """
        Read object from the byte array
        :param byte_array:
        """
        byteorder = get_wdb_byteorder()
        self.code = int.from_bytes(byte_array[0:1], byteorder)
        self.time = int.from_bytes(byte_array[4:8], byteorder)

    def get_bytes(self):
        byteorder = get_wdb_byteorder()
        code = 0
        if str(self.code).isdigit():
            code = int(self.code)
        return code.to_bytes(4, byteorder) + self.time.to_bytes(4, byteorder)


class WDBFinish:
    def __init__(self):
        self.number = 0
        self.time = 0
        self.sound = 0

    def parse_bytes(self, byte_array):
        """
        Read object from the byte array
        :param byte_array:
        """
        byteorder = get_wdb_byteorder()
        self.number = int.from_bytes(byte_array[0:4], byteorder)
        self.time = int.from_bytes(byte_array[4:8], byteorder)
        self.sound = int.from_bytes(byte_array[8:12], byteorder)

    def create(self, number, time, sound):
        self.number = number
        self.time = time
        self.sound = sound

    def get_bytes(self):
        byteorder = get_wdb_byteorder()
        ret = bytearray()
        ret += self.number.to_bytes(4, byteorder)
        ret += self.time.to_bytes(4, byteorder)
        ret += self.sound.to_bytes(4, byteorder)
        return ret


class WDBChip:
    def __init__(self):
        self.id = 0
        self.start_number = 0
        self.quantity = 0
        self.start = WDBPunch()
        self.finish = WDBPunch()
        self.check = WDBPunch()
        self.clear = WDBPunch()
        self.punch = []

    def parse_bytes(self, byte_array, is_new_format=True):
        """
        Read object from the byte array
        :param is_new_format:
        :param byte_array:
        """
        byteorder = get_wdb_byteorder()
        self.id = int.from_bytes(byte_array[0:4], byteorder)
        self.start_number = int.from_bytes(byte_array[4:8], byteorder)
        self.quantity = int.from_bytes(byte_array[8:12], byteorder)
        self.start.parse_bytes(byte_array[12:20])
        self.finish.parse_bytes(byte_array[20:28])
        self.check.parse_bytes(byte_array[28:36])
        self.clear.parse_bytes(byte_array[36:44])

        punch_limit = 200
        if not is_new_format:
            punch_limit = 64
        for i in range(punch_limit):
            new_obj = WDBPunch()
            new_obj.parse_bytes(byte_array[44 + i * 8 : 52 + i * 8])
            self.punch.append(new_obj)

    def get_bytes(self, is_new_format=True):
        byteorder = get_wdb_byteorder()
        ret = int(self.id).to_bytes(4, byteorder)
        ret += int(self.start_number).to_bytes(4, byteorder)
        ret += int(self.quantity).to_bytes(4, byteorder)
        ret += self.start.get_bytes()
        ret += self.finish.get_bytes()
        ret += self.check.get_bytes()
        ret += self.clear.get_bytes()

        punch_limit = 200
        if not is_new_format:
            punch_limit = 64

        for i in range(punch_limit):
            if i < len(self.punch):
                current_punch = self.punch[i]
            else:
                current_punch = WDBPunch()
            if isinstance(current_punch, WDBPunch):
                ret += current_punch.get_bytes()
        return ret


class WDBTeam:
    def __init__(self):
        self.id = 0
        self.name = '_'
        self.refferent = ''
        self.country = 0
        self.region = 0
        self.people_in_base = 0
        self.people_finished = 0
        self.people_selected = 0
        self.is_selected = False
        self.unused = 0  # most likely it's region code

    def parse_bytes(self, byte_array):
        """
        Read object from the byte array
        :param byte_array:
        """
        byteorder = get_wdb_byteorder()

        self.id = int.from_bytes(byte_array[0:4], byteorder)
        self.name = encode(byte_array[4:25])
        self.refferent = encode(byte_array[25:44])
        self.country = int.from_bytes(byte_array[44:45], byteorder)
        self.region = int.from_bytes(byte_array[45:46], byteorder)
        self.people_in_base = int.from_bytes(byte_array[46:48], byteorder)
        self.people_finished = int.from_bytes(byte_array[48:50], byteorder)
        self.people_selected = int.from_bytes(byte_array[50:52], byteorder)
        self.is_selected = byte_array[52] == 0x01
        self.unused = int.from_bytes(byte_array[54:56], byteorder)

    def get_bytes(self):
        byteorder = get_wdb_byteorder()

        ret = int(self.id).to_bytes(4, byteorder)
        ret += format_string_to_bytes(self.name, 21)
        ret += format_string_to_bytes(self.refferent, 19)
        ret += int(self.country).to_bytes(1, byteorder)
        ret += int(self.region).to_bytes(1, byteorder)
        ret += int(self.people_in_base).to_bytes(2, byteorder)
        ret += int(self.people_finished).to_bytes(2, byteorder)
        ret += int(self.people_selected).to_bytes(2, byteorder)
        ret += bool(self.is_selected).to_bytes(2, byteorder)
        ret += int(self.unused).to_bytes(2, byteorder)

        return ret


class WDBDistance:
    def __init__(self):
        self.id = 0
        self.name = '_'
        self.biathlon_columns = ''
        self.point = [100]
        self.leg = [100]
        self.length = 0
        self.corridor = 0
        self.point_quantity = 0
        self.elevation = 0
        self.time_limit = 0
        self.first_cp_free_order = 0
        self.penalty_seconds = 0
        self.people_in_base = 0
        self.people_finished = 0
        self.people_selected = 0
        self.is_selected = False

    def parse_bytes(self, byte_array):
        """
        Read object from the byte array
        :param byte_array:
        """
        byteorder = get_wdb_byteorder()
        max_point_qty = 100

        self.id = int.from_bytes(byte_array[0:4], byteorder)
        self.name = encode(byte_array[4:11])
        self.biathlon_columns = encode(byte_array[11:16])
        self.point.clear()
        self.leg.clear()
        for i in range(max_point_qty):
            self.point.append(int.from_bytes(byte_array[16 + i : 17 + i], byteorder))
            self.leg.append(
                int.from_bytes(byte_array[116 + i * 2 : 118 + i * 2], byteorder)
            )
        self.length = int.from_bytes(byte_array[316:320], byteorder)
        self.corridor = int.from_bytes(byte_array[320:324], byteorder)
        self.point_quantity = int.from_bytes(byte_array[324:328], byteorder)
        self.elevation = int.from_bytes(byte_array[328:332], byteorder)
        self.time_limit = int.from_bytes(byte_array[332:336], byteorder)
        self.first_cp_free_order = int.from_bytes(byte_array[336:340], byteorder)
        self.penalty_seconds = int.from_bytes(byte_array[340:344], byteorder)
        self.people_in_base = int.from_bytes(byte_array[344:346], byteorder)
        self.people_finished = int.from_bytes(byte_array[346:348], byteorder)
        self.people_selected = int.from_bytes(byte_array[348:350], byteorder)
        self.is_selected = byte_array[350] == 0x01

    def get_bytes(self):
        byteorder = get_wdb_byteorder()

        max_point_qty = 100

        ret = int(self.id).to_bytes(4, byteorder)
        ret += format_string_to_bytes(self.name, 7)
        ret += format_string_to_bytes(self.biathlon_columns, 5)
        for i in range(max_point_qty):
            if len(self.point) > i:
                ret += self.point[i].to_bytes(1, byteorder)
            else:
                ret += int(0).to_bytes(1, byteorder)
        for i in range(max_point_qty):
            if len(self.leg) > i:
                ret += self.leg[i].to_bytes(2, byteorder)
            else:
                ret += int(0).to_bytes(2, byteorder)
        ret += self.length.to_bytes(4, byteorder)
        ret += self.corridor.to_bytes(4, byteorder)
        ret += self.point_quantity.to_bytes(4, byteorder)
        ret += self.elevation.to_bytes(4, byteorder)
        ret += self.time_limit.to_bytes(4, byteorder)
        ret += self.first_cp_free_order.to_bytes(4, byteorder)
        ret += self.penalty_seconds.to_bytes(4, byteorder)
        ret += self.people_in_base.to_bytes(2, byteorder)
        ret += self.people_finished.to_bytes(2, byteorder)
        ret += self.people_selected.to_bytes(2, byteorder)
        ret += self.is_selected.to_bytes(1, byteorder)
        ret += format_string_to_bytes('~', 1)

        return ret


class WDBGroup:
    def __init__(self):
        self.id = 0
        self.name = '_'
        self.qual_kms = 0
        self.qual_ms = 0
        self.distance_id = 0
        self.people_in_base = 0
        self.people_finished = 0
        self.people_selected = 0
        self.qual_mode = 0
        self.rent_cost = 0
        self.rent_discount_cost = 0
        self.owner_cost = 0
        self.owner_discount_cost = 0
        self.unused1 = 0
        self.wdb = None

    def parse_bytes(self, byte_array):
        """
        Read object from the byte array
        :param byte_array:
        """
        byteorder = get_wdb_byteorder()

        self.id = int.from_bytes(byte_array[0:4], byteorder)
        self.name = encode(byte_array[4:14])
        self.qual_kms = int.from_bytes(byte_array[13:14], byteorder)
        self.qual_ms = int.from_bytes(byte_array[14:15], byteorder)
        self.distance_id = int.from_bytes(byte_array[16:18], byteorder)
        self.people_in_base = int.from_bytes(byte_array[18:20], byteorder)
        self.people_finished = int.from_bytes(byte_array[20:22], byteorder)
        self.people_selected = int.from_bytes(byte_array[22:24], byteorder)
        self.qual_mode = int.from_bytes(byte_array[24:25], byteorder)
        self.rent_cost = int.from_bytes(byte_array[26:28], byteorder)
        self.rent_discount_cost = int.from_bytes(byte_array[28:30], byteorder)
        self.owner_cost = int.from_bytes(byte_array[30:32], byteorder)
        self.owner_discount_cost = int.from_bytes(byte_array[32:34], byteorder)
        self.unused1 = int.from_bytes(byte_array[34:36], byteorder)

    def get_bytes(self):
        byteorder = get_wdb_byteorder()

        ret = int(self.id).to_bytes(4, byteorder)
        ret += format_string_to_bytes(self.name, 9)
        ret += int(self.qual_kms).to_bytes(1, byteorder)
        ret += int(self.qual_kms).to_bytes(1, byteorder)
        ret += int(0).to_bytes(1, byteorder)
        ret += int(self.distance_id).to_bytes(2, byteorder)
        ret += int(self.people_in_base).to_bytes(2, byteorder)
        ret += int(self.people_finished).to_bytes(2, byteorder)
        ret += int(self.people_selected).to_bytes(2, byteorder)
        ret += int(self.qual_mode).to_bytes(2, byteorder)
        ret += int(self.rent_cost).to_bytes(2, byteorder)
        ret += int(self.rent_discount_cost).to_bytes(2, byteorder)
        ret += int(self.owner_cost).to_bytes(2, byteorder)
        ret += int(self.owner_discount_cost).to_bytes(2, byteorder)
        ret += int(self.unused1).to_bytes(2, byteorder)

        return ret

    def get_course(self):
        if self.wdb:
            return self.wdb.find_course_by_id(self.distance_id)
        return None


class WDBMan:
    def __init__(self, wdb):
        self.name = '_'
        self.comment = '_'
        self.year = 0
        self.qualification = 0
        self.group = 0
        self.team = 0
        self.number = 0
        self.start = 0
        self.finish = 0
        self.result = 0
        self.si_card = 0
        self.id = 0
        self.finished = 0
        self.is_checked = False
        self.is_not_qualified = False
        self.is_without_team = False
        self.unknown0 = 0
        self.is_own_card = 0
        self.unknown2 = 0
        self.status = 0
        self.start_group = 0
        self.penalty_second = 0
        self.wdb = wdb

    def parse_bytes(self, byte_array):
        """
        Read object from the byte array
        :param byte_array:
        """
        byteorder = get_wdb_byteorder()

        self.name = encode(byte_array[0:25])
        self.comment = encode(byte_array[26:46])
        self.year = int.from_bytes(byte_array[48:50], byteorder)
        self.qualification = int.from_bytes(byte_array[50:52], byteorder)
        self.group = int.from_bytes(byte_array[52:54], byteorder)
        self.team = int.from_bytes(byte_array[54:56], byteorder)
        self.unknown0 = int.from_bytes(byte_array[56:57], byteorder)

        self.number = int.from_bytes(byte_array[58:60], byteorder)
        self.start = int.from_bytes(byte_array[60:64], byteorder)
        self.finish = int.from_bytes(byte_array[64:68], byteorder)
        self.result = int.from_bytes(byte_array[68:72], byteorder)

        self.penalty_second = int.from_bytes(byte_array[80:82], byteorder)
        self.finished = int.from_bytes(byte_array[82:83], byteorder)

        self.si_card = int.from_bytes(byte_array[88:92], byteorder)
        self.id = int.from_bytes(byte_array[92:96], byteorder)
        self.is_checked = byte_array[96] == 0x01
        self.is_not_qualified = byte_array[97] == 0x01
        self.is_without_team = byte_array[98] == 0x01

        self.is_own_card = int.from_bytes(byte_array[100:101], byteorder)

        self.unknown2 = int.from_bytes(byte_array[104:105], byteorder)

        self.status = int.from_bytes(byte_array[108:109], byteorder)

        self.start_group = int.from_bytes(byte_array[156:160], byteorder)

    def get_bytes(self):
        byteorder = get_wdb_byteorder()

        ret = bytearray()
        for i in range(196):
            ret.append(0)

        ret[0:25] = format_string_to_bytes(self.name, 25)
        ret[26:46] = format_string_to_bytes(self.comment, 20)
        ret[48:50] = self.year.to_bytes(2, byteorder)
        ret[50:52] = self.qualification.to_bytes(2, byteorder)
        ret[52:54] = self.group.to_bytes(2, byteorder)
        ret[54:56] = self.team.to_bytes(2, byteorder)
        ret[56:57] = self.unknown0.to_bytes(1, byteorder)

        ret[58:60] = self.number.to_bytes(2, byteorder)
        ret[60:64] = self.start.to_bytes(4, byteorder)
        ret[64:68] = self.finish.to_bytes(4, byteorder)
        ret[68:72] = self.result.to_bytes(4, byteorder)

        ret[80:82] = self.penalty_second.to_bytes(2, byteorder)
        ret[82:83] = self.finished.to_bytes(1, byteorder)

        if self.si_card:
            ret[88:92] = self.si_card.to_bytes(4, byteorder)
        ret[92:96] = self.id.to_bytes(4, byteorder)
        ret[96:97] = self.is_checked.to_bytes(1, byteorder)
        ret[97:98] = self.is_not_qualified.to_bytes(1, byteorder)
        ret[98:99] = self.is_without_team.to_bytes(1, byteorder)

        ret[100:101] = self.is_own_card.to_bytes(1, byteorder)

        ret[104:105] = self.unknown2.to_bytes(1, byteorder)

        ret[108:109] = self.status.to_bytes(1, byteorder)

        ret[156:160] = self.start_group.to_bytes(4, byteorder)

        return ret

    def get_group(self):
        if self.wdb:
            return self.wdb.find_group_by_id(self.group)
        return None

    def get_finish(self):
        if self.wdb:
            return self.wdb.find_finish_by_number(self.number)
        return None

    def get_team(self):
        if self.wdb:
            return self.wdb.find_team_by_id(self.team)
        return None

    def get_chip(self):
        if self.wdb:
            return self.wdb.find_chip_by_id(self.si_card)
        return None


class WDBInfo:
    def __init__(self):
        self.title = (
            []
        )  # Name of competition, sponsors, organizers. 10 lines * 80 chars
        self.place = ''  # Competition venue, 25 chars
        self.referee = ''  # Name of responsible referee - senior event adviser
        self.secretary = ''  # Name of secretary
        self.date_str = ''  # Date of competition, as string
        self.type = 0  # Type of competition
        self.relay_type = 0  # Type of relay
        self.distance_service = []  # Course setters, advisers
        self.team_filer = 0  # Team, selected in filter dialog. 0 if no filter applied
        self.group_filter = (
            0  # Group, selected in filter dialog. 0 if no filter applied
        )
        self.filter_selection = 0  # Selecton for filter - any/yes/no
        self.filter_stage = 0  # Filer of relay stages
        self.last_set_number = 0  # Last start number, assigned by application
        self.number_interval = 1  # Interval between start numbers
        self.last_set_start = 0  # Last start time, assigned by application
        self.start_interval = 0  # Interval between start  times
        self.sort_type = 0  # Type of sorting
        self.is_print_speed = False  # Print speed in splint printout
        self.is_print_split_place = False  # Print results - print place for each leg
        self.is_print_cost = False
        self.is_print_selected_only = False  #
        self.is_print_splits = False
        self.is_print_distance = False
        self.is_print_all_splits = False
        self.is_print_card_info = False
        self.toss_who = 0
        self.is_toss_start_group = False
        self.is_toss_teams = False
        self.print_start_who = 0
        self.is_print_start_si = False
        self.is_manual_si = False
        self.is_print_course_setter = False
        self.point_factor_a = 0
        self.point_factor_b = 0
        self.point_factor_c = 0
        self.result_print_who = 0
        self.result_print_best_qty = 0
        self.is_print_course_setter2 = False
        self.is_sound_on = False
        self.filter_team = 0
        self.filter_team2 = 0
        self.filter_group = 0
        self.filter_lap = 0
        self.is_filter_used = False
        self.current_position = 0
        self.print_target = 0
        self.view_offset = 0
        self.si_start_time = 0
        self.is_print_limit_time = False
        self.si_finish_source = 0
        self.si_start_source = 0
        self.si_check_mode = 0
        self.is_split_printout = False
        self.is_split_printout_second_for_dsq = False
        self.split_print_offset = 0
        self.is_autosave = True
        self.current_mode = 0
        self.is_print_perfomance = False
        self.is_online_print_lap = False
        self.com_port = 0
        self.is_sound_team = False
        self.is_sound_group = False
        self.is_result_print_all_finishes = False
        self.is_result_print_si = False
        self.precision = 0
        self.is_result_print_non_started = False
        self.is_result_print_cp_number = False
        self.current_day = 0
        self.is_result_print_lap = False
        self.is_write_scores = False
        self.is_relay_complete_to_4_digits = False
        self.is_chip_warning = False
        self.who_perfomance = 0
        self.who_print_results = 0
        self.is_limit_time_dsq = 0
        self.is_print_result_new_page = False
        self.is_print_relay_variant = False
        self.is_pursuit_start_time = False
        self.team_time = 0
        self.group_time = 0
        self.person_time = 0
        self.point_penalty = 0
        self.multi_day = []
        self.is_print_relay_number_dashed = False  # 123-1 for relay number
        self.is_si_usb = True  # Baudrate for BSM-7/8: 0 - COM, 1 - USB
        self.is_get_score_personally = False
        self.dsq_reason = []
        self.dsq_text = []
        self.note = ''
        self.is_print_note = False
        self.is_print_event_code = False
        self.is_print_comment = False
        self.reserve = []  # Reserve block, not used
        self.online_url = ''  # URL of online sending. Up to 59 chars
        self.server_name = ''  # Name of server for client-server mode. Up to 14 chars
        self.server_sending_mode = (
            0  # Mode of client-server work: background, si reading, manual
        )
        self.unknown1 = 0
        self.is_labirint_mode = False

    def parse_bytes(self, byte_array):
        """
        Read object from the byte array
        :param byte_array:
        """
        byteorder = get_wdb_byteorder()

        self.title.clear()
        for i in range(10):
            self.title.append(encode(byte_array[i * 80 : (i + 1) * 80]))
        self.place = encode(byte_array[800:825])
        self.secretary = encode(byte_array[825:850])
        self.referee = encode(byte_array[850:875])
        self.date_str = encode(byte_array[875:896])
        self.type = int.from_bytes(byte_array[896:897], byteorder)
        self.relay_type = int.from_bytes(byte_array[897:898], byteorder)
        for i in range(4):
            self.distance_service.append(
                encode(byte_array[898 + i * 25 : 923 + i * 25])
            )
        self.team_filer = int.from_bytes(byte_array[998:1000], byteorder)
        self.group_filter = int.from_bytes(byte_array[1000:1002], byteorder)
        self.filter_selection = int.from_bytes(byte_array[1002:1003], byteorder)
        self.filter_stage = int.from_bytes(byte_array[1003:1004], byteorder)

        self.last_set_number = int.from_bytes(byte_array[1016:1018], byteorder)
        self.number_interval = int.from_bytes(byte_array[1018:1020], byteorder)
        self.last_set_start = int.from_bytes(byte_array[1020:1024], byteorder)
        self.start_interval = int.from_bytes(byte_array[1024:1028], byteorder)
        self.sort_type = int.from_bytes(byte_array[1028:1029], byteorder)
        self.is_print_speed = byte_array[1029] == 0x01
        self.is_print_split_place = byte_array[1030] == 0x01
        self.is_print_cost = byte_array[1031] == 0x01
        self.is_print_selected_only = byte_array[1032] == 0x01
        self.is_print_splits = byte_array[1033] == 0x01
        self.is_print_distance = byte_array[1034] == 0x01
        self.is_print_all_splits = byte_array[1035] == 0x01
        self.is_print_card_info = byte_array[1036] == 0x01
        self.toss_who = int.from_bytes(byte_array[1037:1038], byteorder)
        self.is_toss_start_group = byte_array[1038] == 0x01
        self.is_toss_teams = byte_array[1039] == 0x01
        self.print_start_who = int.from_bytes(byte_array[1040:1041], byteorder)
        self.is_print_start_si = byte_array[1041] == 0x01
        self.is_manual_si = byte_array[1042] == 0x01
        self.is_print_course_setter = byte_array[1043] == 0x01
        self.point_factor_a = int.from_bytes(byte_array[1044:1048], byteorder)
        self.point_factor_b = int.from_bytes(byte_array[1048:1052], byteorder)
        self.point_factor_c = int.from_bytes(byte_array[1052:1056], byteorder)
        self.result_print_who = int.from_bytes(byte_array[1056:1057], byteorder)
        self.result_print_best_qty = int.from_bytes(byte_array[1057:1058], byteorder)
        self.is_print_course_setter2 = byte_array[1058] == 0x01
        self.is_sound_on = byte_array[1059] == 0x01
        self.filter_team2 = int.from_bytes(byte_array[1060:1061], byteorder)
        self.filter_group = int.from_bytes(byte_array[1061:1062], byteorder)
        self.filter_lap = int.from_bytes(byte_array[1062:1063], byteorder)
        self.is_filter_used = byte_array[1063] == 0x01
        self.current_position = int.from_bytes(byte_array[1064:1065], byteorder)
        self.print_target = int.from_bytes(byte_array[1065:1066], byteorder)
        self.view_offset = int.from_bytes(byte_array[1066:1067], byteorder)

        self.si_start_time = int.from_bytes(byte_array[1072:1076], byteorder)
        self.is_print_limit_time = byte_array[1076] == 0x01
        self.si_finish_source = int.from_bytes(byte_array[1077:1078], byteorder)
        self.si_start_source = int.from_bytes(byte_array[1078:1079], byteorder)
        self.si_check_mode = int.from_bytes(byte_array[1079:1080], byteorder)
        self.is_print_splits = byte_array[1080] == 0x01
        self.is_split_printout_second_for_dsq = byte_array[1081] == 0x01
        self.split_print_offset = int.from_bytes(byte_array[1082:1083], byteorder)
        self.is_autosave = byte_array[1083] == 0x01
        self.current_mode = int.from_bytes(byte_array[1084:1085], byteorder)
        self.is_print_perfomance = byte_array[1085] == 0x01
        self.is_online_print_lap = byte_array[1086] == 0x01
        self.com_port = int.from_bytes(byte_array[1087:1088], byteorder)
        self.is_sound_team = byte_array[1088] == 0x01
        self.is_sound_group = byte_array[1089] == 0x01
        self.is_result_print_all_finishes = byte_array[1090] == 0x01
        self.is_result_print_si = byte_array[1091] == 0x01
        self.precision = int.from_bytes(byte_array[1092:1093], byteorder)
        self.is_result_print_non_started = byte_array[1093] == 0x01
        self.is_result_print_cp_number = byte_array[1094] == 0x01
        self.current_day = int.from_bytes(byte_array[1095:1096], byteorder)
        self.is_result_print_lap = byte_array[1096] == 0x01
        self.is_write_scores = byte_array[1097] == 0x01
        self.is_relay_complete_to_4_digits = byte_array[1098] == 0x01
        self.is_chip_warning = byte_array[1099] == 0x01
        self.who_perfomance = int.from_bytes(byte_array[1100:1101], byteorder)
        self.who_print_results = int.from_bytes(byte_array[1101:1102], byteorder)

        self.is_limit_time_dsq = byte_array[1103] == 0x01
        self.is_print_result_new_page = byte_array[1104] == 0x01
        self.is_print_relay_variant = byte_array[1105] == 0x01
        self.is_pursuit_start_time = byte_array[1106] == 0x01
        self.unknown1 = int.from_bytes(byte_array[1107:1108], byteorder)
        self.team_time = int.from_bytes(byte_array[1108:1112], byteorder)
        self.group_time = int.from_bytes(byte_array[1112:1116], byteorder)
        self.person_time = int.from_bytes(byte_array[1116:1120], byteorder)
        self.point_penalty = int.from_bytes(byte_array[1120:1124], byteorder)
        self.multi_day.clear()
        for i in range(10):
            self.multi_day.append(byte_array[1124 + i] == 0x01)
        self.is_print_relay_number_dashed = byte_array[1134] == 0x01
        self.is_si_usb = byte_array[1135] == 0x01
        self.is_get_score_personally = byte_array[1136] == 0x01
        dsq_count = 9
        dsq_size = 12
        for i in range(dsq_count):
            self.dsq_reason.append(
                encode(byte_array[1137 + i * dsq_size : 1137 + i * dsq_size + dsq_size])
            )
            self.dsq_text.append(
                encode(byte_array[1245 + i * dsq_size : 1245 + i * dsq_size + dsq_size])
            )
        self.note = encode(byte_array[1353:1453])
        self.is_print_note = byte_array[1453] == 0x01
        self.is_print_event_code = byte_array[1454] == 0x01
        self.is_print_comment = byte_array[1455] == 0x01
        self.reserve.clear()
        for i in range(10):
            self.reserve.append(
                int.from_bytes(byte_array[1456 + i : 1457 + i], byteorder)
            )
        self.online_url = encode(byte_array[1466:1525])
        self.server_name = encode(byte_array[1526:1540])
        self.server_sending_mode = int.from_bytes(byte_array[1541:1542], byteorder)
        self.is_labirint_mode = byte_array[1555] == 0x01

    def get_bytes(self):
        byteorder = get_wdb_byteorder()

        ret = bytearray()
        for i in range(1556):
            ret.append(0)

        for i in range(10):
            string = ''
            if len(self.title) > i:
                string = self.title[i]
            ret[i * 80 : (i + 1) * 80] = format_string_to_bytes(string, 80)
        ret[800:825] = format_string_to_bytes(self.place, 25)
        ret[825:850] = format_string_to_bytes(self.referee, 25)
        ret[850:875] = format_string_to_bytes(self.secretary, 25)
        ret[875:896] = format_string_to_bytes(self.date_str, 21)
        ret[896:897] = self.type.to_bytes(1, byteorder)
        ret[897:898] = self.relay_type.to_bytes(1, byteorder)
        obj_size = 25
        for i in range(4):
            string = ''
            if len(self.distance_service) > i:
                string = self.distance_service[i]
            ret[898 + i * obj_size : 898 + (i + 1) * obj_size] = format_string_to_bytes(
                string, obj_size
            )
        ret[998:1000] = self.filter_team.to_bytes(2, byteorder)
        ret[1000:1002] = self.filter_group.to_bytes(2, byteorder)
        ret[1002:1003] = self.filter_selection.to_bytes(1, byteorder)
        ret[1004:1005] = self.filter_stage.to_bytes(1, byteorder)
        ret[1016:1018] = self.last_set_number.to_bytes(2, byteorder)
        ret[1018:1020] = self.number_interval.to_bytes(2, byteorder)
        ret[1020:1024] = self.last_set_start.to_bytes(4, byteorder)
        ret[1024:1028] = self.start_interval.to_bytes(4, byteorder)
        ret[1028:1029] = self.sort_type.to_bytes(1, byteorder)
        ret[1029:1030] = self.is_print_speed.to_bytes(1, byteorder)
        ret[1030:1031] = self.is_print_split_place.to_bytes(1, byteorder)
        ret[1031:1032] = self.is_print_cost.to_bytes(1, byteorder)
        ret[1032:1033] = self.is_print_selected_only.to_bytes(1, byteorder)
        ret[1033:1034] = self.is_print_splits.to_bytes(1, byteorder)
        ret[1034:1035] = self.is_print_distance.to_bytes(1, byteorder)
        ret[1035:1036] = self.is_print_all_splits.to_bytes(1, byteorder)
        ret[1036:1037] = self.is_print_card_info.to_bytes(1, byteorder)
        ret[1037:1038] = self.toss_who.to_bytes(1, byteorder)
        ret[1038:1039] = self.is_toss_start_group.to_bytes(1, byteorder)
        ret[1039:1040] = self.is_toss_teams.to_bytes(1, byteorder)
        ret[1040:1041] = self.print_start_who.to_bytes(1, byteorder)
        ret[1041:1042] = self.is_print_start_si.to_bytes(1, byteorder)
        ret[1042:1043] = self.is_manual_si.to_bytes(1, byteorder)
        ret[1043:1044] = self.is_print_course_setter.to_bytes(1, byteorder)
        ret[1044:1048] = self.point_factor_a.to_bytes(4, byteorder)
        ret[1048:1052] = self.point_factor_b.to_bytes(4, byteorder)
        ret[1052:1056] = self.point_factor_c.to_bytes(4, byteorder)
        ret[1056:1057] = self.result_print_who.to_bytes(1, byteorder)
        ret[1057:1058] = self.result_print_best_qty.to_bytes(1, byteorder)
        ret[1058:1059] = self.is_print_course_setter2.to_bytes(1, byteorder)
        ret[1059:1060] = self.is_sound_on.to_bytes(1, byteorder)
        ret[1060:1061] = self.filter_team2.to_bytes(1, byteorder)
        ret[1061:1062] = self.filter_group.to_bytes(1, byteorder)
        ret[1062:1063] = self.filter_lap.to_bytes(1, byteorder)
        ret[1063:1064] = self.is_filter_used.to_bytes(1, byteorder)
        ret[1064:1065] = self.current_position.to_bytes(1, byteorder)
        ret[1065:1066] = self.print_target.to_bytes(1, byteorder)
        ret[1066:1067] = self.split_print_offset.to_bytes(1, byteorder)
        ret[1072:1076] = self.si_start_time.to_bytes(4, byteorder)
        ret[1076:1077] = self.is_print_limit_time.to_bytes(1, byteorder)
        ret[1077:1078] = self.si_finish_source.to_bytes(1, byteorder)
        ret[1078:1079] = self.si_start_source.to_bytes(1, byteorder)
        ret[1079:1080] = self.si_check_mode.to_bytes(1, byteorder)
        ret[1080:1081] = self.is_print_card_info.to_bytes(1, byteorder)
        ret[1081:1082] = self.is_split_printout_second_for_dsq.to_bytes(1, byteorder)
        ret[1082:1083] = self.split_print_offset.to_bytes(1, byteorder)
        ret[1083:1084] = self.is_autosave.to_bytes(1, byteorder)
        ret[1084:1085] = self.current_mode.to_bytes(1, byteorder)
        ret[1085:1086] = self.is_print_perfomance.to_bytes(1, byteorder)
        ret[1086:1087] = self.is_online_print_lap.to_bytes(1, byteorder)
        ret[1087:1088] = self.com_port.to_bytes(1, byteorder)
        ret[1088:1089] = self.is_sound_team.to_bytes(1, byteorder)
        ret[1089:1090] = self.is_sound_group.to_bytes(1, byteorder)
        ret[1090:1091] = self.is_result_print_all_finishes.to_bytes(1, byteorder)
        ret[1091:1092] = self.is_result_print_si.to_bytes(1, byteorder)
        ret[1092:1093] = self.precision.to_bytes(1, byteorder)
        ret[1093:1094] = self.is_result_print_non_started.to_bytes(1, byteorder)
        ret[1094:1095] = self.is_result_print_cp_number.to_bytes(1, byteorder)
        ret[1095:1096] = self.current_day.to_bytes(1, byteorder)
        ret[1096:1097] = self.is_result_print_lap.to_bytes(1, byteorder)
        ret[1097:1098] = self.is_write_scores.to_bytes(1, byteorder)
        ret[1098:1099] = self.is_relay_complete_to_4_digits.to_bytes(1, byteorder)
        ret[1099:1100] = self.is_chip_warning.to_bytes(1, byteorder)
        ret[1100:1101] = self.who_perfomance.to_bytes(1, byteorder)
        ret[1101:1102] = self.who_print_results.to_bytes(1, byteorder)
        # ret[1102] = self.reserve.to_bytes(1, byteorder)
        ret[1103:1104] = self.is_limit_time_dsq.to_bytes(1, byteorder)
        ret[1104:1105] = self.is_print_result_new_page.to_bytes(1, byteorder)
        ret[1105:1106] = self.is_print_relay_variant.to_bytes(1, byteorder)
        ret[1106:1107] = self.is_pursuit_start_time.to_bytes(1, byteorder)
        ret[1107:1108] = self.unknown1.to_bytes(1, byteorder)
        ret[1108:1112] = self.team_time.to_bytes(4, byteorder)
        ret[1112:1116] = self.group_time.to_bytes(4, byteorder)
        ret[1116:1120] = self.person_time.to_bytes(4, byteorder)
        ret[1120:1124] = self.point_penalty.to_bytes(4, byteorder)
        for i in range(10):
            cur_object = True
            if len(self.multi_day) > i:
                cur_object = self.multi_day[i]
            ret[1124 + i : 1125 + i] = cur_object.to_bytes(1, byteorder)

        ret[1134:1135] = self.is_print_relay_number_dashed.to_bytes(1, byteorder)
        ret[1135:1136] = self.is_si_usb.to_bytes(1, byteorder)
        ret[1136:1137] = self.is_get_score_personally.to_bytes(1, byteorder)
        obj_size = 12
        for i in range(9):
            dsq_reason = ''
            dsq_text = ''
            if len(dsq_reason) > i:
                dsq_reason = self.dsq_reason[i]
                dsq_text = self.dsq_text[i]
            ret[
                1137 + i * obj_size : 1137 + (i + 1) * obj_size
            ] = format_string_to_bytes(dsq_reason, obj_size)
            ret[
                1245 + i * obj_size : 1245 + (i + 1) * obj_size
            ] = format_string_to_bytes(dsq_text, obj_size)
        ret[1353:1453] = format_string_to_bytes(self.note, 100)
        ret[1453:1454] = self.is_print_note.to_bytes(1, byteorder)
        ret[1454:1455] = self.is_print_event_code.to_bytes(1, byteorder)
        ret[1455:1456] = self.is_print_comment.to_bytes(1, byteorder)
        for i in range(10):
            cur_object = 0
            if len(self.reserve) > i:
                cur_object = self.reserve[i]
            ret[1456 + i : 1457 + i] = cur_object.to_bytes(1, byteorder)
        ret[1466:1525] = format_string_to_bytes(self.online_url, 59)
        ret[1526:1540] = format_string_to_bytes(self.server_name, 14)
        ret[1541:1542] = self.server_sending_mode.to_bytes(1, byteorder)

        ret[1555:1556] = self.is_labirint_mode.to_bytes(1, byteorder)
        return ret


class WDBAdventure:
    def __init__(self):
        self.group = 0
        self.x = 0
        self.y = 0
        self.scores = 0
        self.mode = 0
        self.description = ''
        self.ideal_time = 0
        self.ideal_scores = 0
        self.min = 0
        self.is_use_cart = False
        self.is_cart_clear = False
        self.is_time_stop = False
        self.time_stop_value = 0
        self.scores_from_file = 0
        self.scores_cart_mode = 0
        self.correct_minutes = 0

    def parse_bytes(self, byte_array):
        """
        Read object from the byte array
        :param byte_array:
        """
        byteorder = get_wdb_byteorder()
        self.group = int.from_bytes(byte_array[0:1], byteorder)

        self.description = encode(byte_array[4:32])
        self.correct_minutes = int.from_bytes(byte_array[33:34], byteorder)

        self.x = int.from_bytes(byte_array[36:40], byteorder)
        self.y = int.from_bytes(byte_array[40:44], byteorder)
        self.scores_from_file = int.from_bytes(byte_array[44:45], byteorder)

        self.mode = byte_array[48] == 0x01

        self.scores = int.from_bytes(byte_array[52:56], byteorder)
        self.ideal_time = int.from_bytes(byte_array[56:60], byteorder)
        self.ideal_scores = int.from_bytes(byte_array[60:64], byteorder)

        self.min = int.from_bytes(byte_array[68:72], byteorder)
        self.is_use_cart = byte_array[72] == 0x01

        self.is_cart_clear = byte_array[76] == 0x01

        self.is_time_stop = byte_array[80] == 0x01

        self.time_stop_value = int.from_bytes(byte_array[84:88], byteorder)

    def get_bytes(self):
        byteorder = get_wdb_byteorder()

        ret = bytearray()
        for i in range(88):
            ret.append(0)

        ret[0:1] = self.group.to_bytes(1, byteorder)
        ret[4:32] = format_string_to_bytes(self.description, 28)
        ret[33:34] = self.correct_minutes.to_bytes(1, byteorder)
        ret[36:40] = self.x.to_bytes(4, byteorder)
        ret[40:44] = self.y.to_bytes(4, byteorder)
        ret[44:45] = self.scores_from_file.to_bytes(1, byteorder)
        ret[48:49] = self.mode.to_bytes(1, byteorder)
        ret[52:56] = self.y.to_bytes(4, byteorder)
        ret[56:60] = self.ideal_time.to_bytes(4, byteorder)
        ret[60:64] = self.ideal_scores.to_bytes(4, byteorder)
        ret[68:72] = self.min.to_bytes(4, byteorder)
        ret[72:73] = self.is_use_cart.to_bytes(1, byteorder)
        ret[76:77] = self.is_cart_clear.to_bytes(1, byteorder)
        ret[80:81] = self.is_time_stop.to_bytes(1, byteorder)
        ret[84:88] = self.time_stop_value.to_bytes(4, byteorder)

        return ret


class WDB:
    def __init__(self):
        self.version = 22
        self.man = []
        self.group = []
        self.team = []
        self.dist = []
        self.fin = []
        self.chip = []
        self.adv = []
        self.info = WDBInfo()

    def parse_bytes(self, byte_array):
        """
        Read object from the byte array
        :param byte_array:
        """
        byteorder = get_wdb_byteorder()
        self.version = int.from_bytes(byte_array[0:4], byteorder)

        #  reading of man objects - int (4 bytes) of quantity + set of 196 byte blocks
        object_size = 196
        initial_start = 4
        qty = int.from_bytes(byte_array[initial_start : initial_start + 4], byteorder)
        initial_start += 4
        end_pos = initial_start
        self.man.clear()
        for i in range(qty):
            start_pos = initial_start + i * object_size
            end_pos = initial_start + (i + 1) * object_size
            new_object = WDBMan(self)
            new_object.parse_bytes(byte_array[start_pos:end_pos])
            self.man.append(new_object)

            if bytes_compare(new_object.get_bytes(), byte_array[start_pos:end_pos]):
                print('Error in Man')

        # reading of team objects - int (4 bytes) of quantity + set of 56 byte blocks
        object_size = 56
        initial_start = end_pos
        qty = int.from_bytes(byte_array[initial_start : initial_start + 4], byteorder)
        initial_start += 4
        end_pos = initial_start
        self.team.clear()
        for i in range(qty):
            start_pos = initial_start + i * object_size
            end_pos = initial_start + (i + 1) * object_size
            new_object = WDBTeam()
            new_object.parse_bytes(byte_array[start_pos:end_pos])
            self.team.append(new_object)

            if bytes_compare(new_object.get_bytes(), byte_array[start_pos:end_pos]):
                print('Error in Team')

        # reading of group objects - int (4 bytes) of quantity + set of 36 byte blocks
        object_size = 36
        initial_start = end_pos
        qty = int.from_bytes(byte_array[initial_start : initial_start + 4], byteorder)
        initial_start += 4
        end_pos = initial_start
        self.group.clear()
        for i in range(qty):
            start_pos = initial_start + i * object_size
            end_pos = initial_start + (i + 1) * object_size
            new_object = WDBGroup()
            new_object.wdb = self
            new_object.parse_bytes(byte_array[start_pos:end_pos])
            self.group.append(new_object)

            if bytes_compare(new_object.get_bytes(), byte_array[start_pos:end_pos]):
                print('Error in Group')

        # reading of course objects - int (4 bytes) of quantity + set of 352 byte blocks
        object_size = 352
        initial_start = end_pos
        qty = int.from_bytes(byte_array[initial_start : initial_start + 4], byteorder)
        initial_start += 4
        end_pos = initial_start
        self.dist.clear()
        for i in range(qty):
            start_pos = initial_start + i * object_size
            end_pos = initial_start + (i + 1) * object_size
            new_object = WDBDistance()
            new_object.parse_bytes(byte_array[start_pos:end_pos])
            self.dist.append(new_object)

            if bytes_compare(new_object.get_bytes(), byte_array[start_pos:end_pos]):
                print('Error in Distance')

        # reading of info block - 1556 bytes
        object_size = 1556
        start_pos = end_pos
        end_pos = start_pos + object_size
        self.info = WDBInfo()
        self.info.parse_bytes(byte_array[start_pos:end_pos])

        if bytes_compare(self.info.get_bytes(), byte_array[start_pos:end_pos]):
            print('Error in Info')

        #  reading of finish objects - int (4 bytes) of quantity + set of 12 byte blocks
        object_size = 12
        initial_start = end_pos
        qty = int.from_bytes(byte_array[initial_start : initial_start + 4], byteorder)
        initial_start += 4
        end_pos = initial_start
        self.fin.clear()
        for i in range(qty):
            start_pos = initial_start + i * object_size
            end_pos = initial_start + (i + 1) * object_size
            new_object = WDBFinish()
            new_object.parse_bytes(byte_array[start_pos:end_pos])
            self.fin.append(new_object)

            if bytes_compare(new_object.get_bytes(), byte_array[start_pos:end_pos]):
                print('Error in Finish')

        initial_start = end_pos
        si_punch_count = 64  # format changing of 2009/03-2010/09: 64 -> 200 punches + added Adventure block

        qty = int.from_bytes(byte_array[initial_start : initial_start + 4], byteorder)
        initial_start += 4
        if qty == 0:
            check = int.from_bytes(
                byte_array[initial_start : initial_start + 4], byteorder
            )
            if check == 257:
                si_punch_count = 200

                # reading of adventure objects - int (4 bytes) of quantity + set of 88 byte blocks
                object_size = 88
                initial_start += 4
                end_pos = initial_start
                self.adv.clear()
                for i in range(check):
                    start_pos = initial_start + i * object_size
                    end_pos = initial_start + (i + 1) * object_size
                    new_object = WDBAdventure()
                    new_object.parse_bytes(byte_array[start_pos:end_pos])
                    self.adv.append(new_object)

                    if bytes_compare(
                        new_object.get_bytes(), byte_array[start_pos:end_pos]
                    ):
                        print('Error in Adventure object')

                initial_start = end_pos
            qty = int.from_bytes(
                byte_array[initial_start : initial_start + 4], byteorder
            )
            initial_start += 4

        # reading of chip objects - int (4 bytes) of quantity + set of 1644 (556 for old format) byte blocks
        object_size = 44 + 8 * si_punch_count
        self.chip.clear()
        for i in range(qty):
            start_pos = initial_start + i * object_size
            end_pos = initial_start + (i + 1) * object_size
            new_object = WDBChip()
            new_object.parse_bytes(byte_array[start_pos:end_pos])
            self.chip.append(new_object)

            if bytes_compare(new_object.get_bytes(), byte_array[start_pos:end_pos]):
                print('Error in Chip object')

    def get_bytes(self, is_new_format=True):

        if len(self.adv) < 1:  # fictive 257 adventure objects
            for i in range(257):
                self.adv.append(WDBAdventure())

        byteorder = get_wdb_byteorder()

        ret = bytearray()
        ret += self.version.to_bytes(4, byteorder)

        ret += len(self.man).to_bytes(4, byteorder)
        for i in self.man:
            ret += i.get_bytes()

        ret += len(self.team).to_bytes(4, byteorder)
        for i in self.team:
            ret += i.get_bytes()

        ret += len(self.group).to_bytes(4, byteorder)
        for i in self.group:
            ret += i.get_bytes()

        ret += len(self.dist).to_bytes(4, byteorder)
        for i in self.dist:
            ret += i.get_bytes()

        ret += self.info.get_bytes()

        ret += len(self.fin).to_bytes(4, byteorder)
        for i in self.fin:
            ret += i.get_bytes()

        if (
            is_new_format
        ):  # format changing of 2009/03-2010/09: 64 -> 200 punches + added Adventure block
            # ret += len(self.chip).to_bytes(4, byteorder)
            ret += int(0).to_bytes(4, byteorder)
            # ret += int(257).to_bytes(4, byteorder)

            ret += len(self.adv).to_bytes(4, byteorder)
            for i in self.adv:
                ret += i.get_bytes()

            ret += len(self.chip).to_bytes(4, byteorder)
            for i in self.chip:
                ret += i.get_bytes()
        else:
            for i in self.chip:
                ret += i.get_bytes(False)

        # ending of wdb file - 20 * 0x00
        for i in range(20):
            ret.append(0)

        return ret

    def find_group_by_id(self, idx):
        for group in self.group:
            if group.id == idx:
                return group
        return None

    def find_group_by_name(self, name):
        for group in self.group:
            if group.name == name:
                return group
        return None

    def find_finish_by_number(self, number):
        for finish in self.fin:
            if finish.number == number:
                return finish
        return None

    def find_team_by_id(self, idx):
        for team in self.team:
            if team.id == idx:
                return team
        return None

    def find_team_by_name(self, name):
        for team in self.team:
            if team.name == name:
                return team
        return None

    def find_chip_by_id(self, idx):
        for chip in self.chip:
            if chip.id == idx:
                return chip
        return None

    def find_course_by_id(self, idx):
        for course in self.dist:
            if course.id == idx:
                return course
        return None

    def find_course_by_name(self, name):
        for course in self.dist:
            if course.name == name:
                return course
        return None

    def find_man_by_name(self, name):
        for man in self.man:
            if man.name == name:
                return man
        return None


def parse_wdb(file_path):
    wdb_file = open(file_path, 'rb')
    byte_array = wdb_file.read()
    wdb_object = WDB()
    wdb_object.parse_bytes(byte_array)

    return wdb_object


def write_wdb(wdb_object, file_path):
    wdb_file = open(file_path, 'wb')
    b_object = wdb_object.get_bytes()
    wdb_file.write(b_object)
    wdb_file.close()
