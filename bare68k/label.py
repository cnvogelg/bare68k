import bare68k.api.label as label


class LabelFormatter(object):

    def format(self, label, pc=None):
        data = label.data()
        # if data is callable
        if callable(data):
            txt = data(pc)
        else:
            txt = data
        # offset?
        off = pc - label.addr()
        if off > 0:
            txt += "+{:x}".format(off)
        return txt


class LabelMgr(object):

    def get_num_labels(self):
        """return total number of labels"""
        return label.get_num_labels()

    def get_num_page_labels(self, page_no):
        """return number of labels on a page"""
        return label.get_num_page_labels(page_no)

    def get_all_labels(self):
        """return all labels"""
        return label.get_all_labels()

    def get_page_labels(self, page_no):
        """return labels stored on a page"""
        return label.get_page_labels(page_no)

    def add_label(self, addr, size, data):
        """add a label for addr range and assign data. return Label object"""
        return label.add_label(addr, size, data)

    def remove_label(self, lbl):
        """remove a label"""
        label.remove_label(lbl)

    def remove_labels_inside(self, addr, size):
        """remove labels inside a region and return the number of removed labels"""
        return label.remove_labels_inside(addr, size)

    def find_label(self, addr):
        """find first label matching addr. return Label object or None"""
        return label.find_label(addr)

    def find_intersecting_labels(self, addr, size):
        """return labels intersecting the given addr range. return [Label]"""
        return label.find_intersecting_labels(addr, size)


class DummyLabelMgr(object):
    """a label mgr implementation that does nothing. useful if labels are disabled"""

    def get_num_labels(self):
        return 0

    def get_num_page_labels(self, page_no):
        return 0

    def get_all_labels(self):
        return None

    def get_page_labels(self, page_no):
        return None

    def add_label(self, addr, size, data):
        return None

    def remove_label(self, label):
        pass

    def remove_labels_inside(self, addr, size):
        return 0

    def find_label(self, addr):
        return None

    def find_intersecting_labels(self, addr, size):
        return None
