from ._getmach import mach

# query labels
get_num_labels = mach.get_num_labels
get_num_page_labels = mach.get_num_page_labels
get_all_labels = mach.get_all_labels
get_page_labels = mach.get_page_labels

# add/remove
add_label = mach.add_label
remove_label = mach.remove_label
remove_labels_inside = mach.remove_labels_inside

# find
find_label = mach.find_label
find_intersecting_labels = mach.find_intersecting_labels
