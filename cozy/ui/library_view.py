from gi.repository import Gtk
from gi.repository.Gtk import Builder

from cozy.ui.book_element import BookElement
from cozy.ui.widgets.filter_list_box import FilterListBox
from cozy.view_model.library_view_model import LibraryViewModel, LibraryViewMode

READER_PAGE = "reader"
AUTHOR_PAGE = "author"
RECENT_PAGE = "recent"
MAIN_BOOK_PAGE = "main"
MAIN_NO_RECENT_PAGE = "nothing_here"


class LibraryView:

    def __init__(self, builder: Builder):
        self._builder = builder

        self._view_model = LibraryViewModel()

        self._get_ui_elements()
        self._connect_ui_elements()

        self._connect_view_model()

        self.populate_book_box()

        self._on_library_view_mode_changed()

    def _get_ui_elements(self):
        self._filter_stack: Gtk.Stack = self._builder.get_object("sort_stack")
        self._main_stack: Gtk.Stack = self._builder.get_object("main_stack")
        self._book_box: Gtk.FlowBox = self._builder.get_object("book_box")
        self._filter_stack_revealer: Gtk.Revealer = self._builder.get_object("sort_stack_revealer")
        self._book_box: Gtk.FlowBox = self._builder.get_object("book_box")
        self._author_box: FilterListBox = self._builder.get_object("author_box")
        self._reader_box: FilterListBox = self._builder.get_object("reader_box")

    def _connect_ui_elements(self):
        self._filter_stack.connect("notify::visible-child", self._on_sort_stack_changed)
        self._book_box.set_sort_func(self._view_model.display_book_sort)
        self._book_box.set_filter_func(self._view_model.display_book_filter)
        self._author_box.connect("row-selected", self._apply_selected_filter)
        self._reader_box.connect("row-selected", self._apply_selected_filter)

    def _connect_view_model(self):
        self._view_model.bind_to("library_view_mode", self._on_library_view_mode_changed)
        self._view_model.bind_to("authors", self.populate_author)
        self._view_model.bind_to("readers", self.populate_reader)
        self._view_model.bind_to("books", self.populate_book_box)
        self._view_model.bind_to("books-filter", self._book_box.invalidate_filter)

    def _on_sort_stack_changed(self, widget, property):
        page = widget.props.visible_child_name

        view_mode = None
        if page == RECENT_PAGE:
            view_mode = LibraryViewMode.CURRENT
        elif page == AUTHOR_PAGE:
            view_mode = LibraryViewMode.AUTHOR
        elif page == READER_PAGE:
            view_mode = LibraryViewMode.READER

        self._view_model.library_view_mode = view_mode

    def populate_book_box(self):
        self._book_box.remove_all_children()

        for book in self._view_model.books:
            book_element = BookElement(book)
            book_element.connect("play-pause-clicked", self._play_book_clicked)
            book_element.connect("open-book-overview", self._open_book_overview_clicked)
            book_element.show_all()
            self._book_box.add(book_element)

    def populate_author(self):
        self._author_box.populate(self._view_model.authors)

    def populate_reader(self):
        self._reader_box.populate(self._view_model.readers)

    def _on_library_view_mode_changed(self):
        visible_child_name = None
        reveal_filter_box = True
        active_filter_box: Gtk.ListBox = None

        view_mode = self._view_model.library_view_mode
        main_view_page = MAIN_BOOK_PAGE

        if view_mode == LibraryViewMode.CURRENT:
            visible_child_name = RECENT_PAGE
            reveal_filter_box = False
            if not self._view_model.is_any_book_in_progress:
                main_view_page = MAIN_NO_RECENT_PAGE
        elif view_mode == LibraryViewMode.AUTHOR:
            visible_child_name = AUTHOR_PAGE
            reveal_filter_box = True
            active_filter_box = self._author_box
        elif view_mode == LibraryViewMode.READER:
            visible_child_name = READER_PAGE
            reveal_filter_box = True
            active_filter_box = self._reader_box

        # https://stackoverflow.com/questions/22178524/gtk-named-stack-childs/22182843#22182843
        self._main_stack.props.visible_child_name = main_view_page
        self._filter_stack.set_visible_child_name(visible_child_name)
        self._filter_stack_revealer.set_reveal_child(reveal_filter_box)

        if active_filter_box:
            self._apply_selected_filter(active_filter_box, active_filter_box.get_selected_row())

        self._invalidate_filters()

    def _invalidate_filters(self):
        self._book_box.invalidate_filter()
        self._book_box.invalidate_sort()

    def _apply_selected_filter(self, sender, row):
        if not row:
            return

        self._view_model.selected_filter = row.data
        self._invalidate_filters()

    def _play_book_clicked(self, widget, book):
        self._view_model.playback_book(book)

    def _open_book_overview_clicked(self, widget, book):
        pass
