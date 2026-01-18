import time
import logging
import idaapi

logger = logging.getLogger("unix-time-format")
logger.setLevel(logging.INFO)


class epoch_format(idaapi.data_format_t):
    FORMAT_NAME = "py_epoch_format"

    def __init__(self, is_local_time, divisor=1):
        """
        Custom data format definition.
        @param name: Format name, must be unique
        @param menu_name: Visible format name to use in menus
        @param props: properties (currently 0)
        @param hotkey: Hotkey for the corresponding menu item
        @param value_size: size of the value in bytes. 0 means any size is ok
        @text_width: Usual width of the text representation
        """

        match divisor:
            case 1:
                self.time_unit = "s"
            case 1000:
                self.time_unit = "ms"
            case 1000000:
                self.time_unit = "us"
            case 1000000000:
                self.time_unit = "ns"
            case _:
                self.time_unit = "s"
                logger.warning(f"Unknown divisor {divisor}, using seconds")
                divisor = 1

        self.divisor = divisor
        self.postfix = "local" if is_local_time else "UTC"
        self.is_local_time = is_local_time

        idaapi.data_format_t.__init__(
            self,
            epoch_format.FORMAT_NAME + self.postfix + self.time_unit,
            4,
            f"Make epoch {self.time_unit} {self.postfix}",
        )

    def printf(self, value_bytes, current_ea, operand_num, dtid):
        #        """
        #        Convert a value buffer to colored string.
        #
        #        @param value: The value to be printed
        #        @param current_ea: The ea of the value
        #        @param operand_num: The affected operand
        #        @param dtid: custom data type id (0-standard built-in data type)
        #        @return: a colored string representing the passed 'value' or None on failure
        #        """
        #        return None
        if len(value_bytes) < 4:
            return None

        value = int.from_bytes(value_bytes, "little")

        if self.is_local_time:
            tm = time.localtime(value / self.divisor)
        else:
            tm = time.gmtime(value / self.divisor)

        time_str = time.strftime("%Y-%m-%d %H:%M:%S %Z", tm)

        return f"epoch_{self.time_unit}( {time_str} )"


# -----------------------------------------------------------------------

# Table of formats and types to be registered/unregistered
# If a tuple has one element then it is the format to be registered with dtid=0
# If the tuple has more than one element, the tuple[0] is the data type and tuple[1:] are the data formats
new_formats = [
    (epoch_format(False),),
    (epoch_format(True),),
    (epoch_format(False, 1000),),
    (epoch_format(True, 1000),),
    (epoch_format(False, 1000000),),
    (epoch_format(True, 1000000),),
    (epoch_format(False, 1000000000),),
    (epoch_format(True, 1000000000),),
]


# -----------------------------------------------------------------------
def nw_handler(code, old=0):
    match code:
        case idaapi.NW_TERMIDA:
            when = idaapi.NW_TERMIDA | idaapi.NW_OPENIDB | idaapi.NW_CLOSEIDB
            idaapi.notify_when(when, nw_handler)

        case idaapi.NW_OPENIDB:
            idaapi.register_data_types_and_formats(new_formats)
        case idaapi.NW_CLOSEIDB:
            idaapi.unregister_data_types_and_formats(new_formats)


def register_epoch_format_handlers():
    if idaapi.find_custom_data_type(epoch_format.FORMAT_NAME + "UTC") != -1:
        logger.debug("Formats already installed")
        return

    if not idaapi.register_data_types_and_formats(new_formats):
        logger.error("Failed to register types")
        return

    idaapi.notify_when(
        idaapi.NW_TERMIDA | idaapi.NW_OPENIDB | idaapi.NW_CLOSEIDB, nw_handler
    )
    logger.debug("Formats installed")


class EpochFormatPlugin(idaapi.plugin_t):
    flags = idaapi.PLUGIN_FIX | idaapi.PLUGIN_HIDE
    comment = "todo comment"
    help = "todo help"
    wanted_name = "epoch formats"
    wanted_hotkey = ""

    def init(self):
        addon = idaapi.addon_info_t()
        addon.id = "milankovo.unix_time_format"
        addon.name = "Unix Time Format"
        addon.producer = "Milankovo"
        addon.url = "https://github.com/milankovo/unix-time-format"
        addon.version = "1.0.0"
        idaapi.register_addon(addon)
        register_epoch_format_handlers()
        return idaapi.PLUGIN_KEEP

    def term(self):
        pass

    def run(self, arg):
        pass


def PLUGIN_ENTRY():
    return EpochFormatPlugin()
