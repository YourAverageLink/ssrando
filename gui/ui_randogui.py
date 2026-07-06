# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'randogui.ui'
##
## Created by: Qt User Interface Compiler version 6.8.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFontComboBox,
    QFrame, QGridLayout, QGroupBox, QHBoxLayout,
    QLabel, QLineEdit, QMainWindow, QPushButton,
    QScrollArea, QSizePolicy, QSpacerItem, QSpinBox,
    QTabWidget, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1202, 766)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        MainWindow.setSizeIncrement(QSize(0, 0))
        font = QFont()
        font.setFamilies([u"Segoe UI"])
        font.setPointSize(9)
        MainWindow.setFont(font)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        sizePolicy.setHeightForWidth(self.centralwidget.sizePolicy().hasHeightForWidth())
        self.centralwidget.setSizePolicy(sizePolicy)
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName(u"tabWidget")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.tabWidget.sizePolicy().hasHeightForWidth())
        self.tabWidget.setSizePolicy(sizePolicy1)
        self.tabWidget.setSizeIncrement(QSize(0, 0))
        self.tabWidget.setToolTipDuration(-6)
        self.tabWidget.setUsesScrollButtons(True)
        self.tabWidget.setDocumentMode(False)
        self.tab_setup = QWidget()
        self.tab_setup.setObjectName(u"tab_setup")
        self.verticalLayout_27 = QVBoxLayout(self.tab_setup)
        self.verticalLayout_27.setObjectName(u"verticalLayout_27")
        self.vlay_files = QVBoxLayout()
        self.vlay_files.setObjectName(u"vlay_files")
        self.hlay_output = QHBoxLayout()
        self.hlay_output.setObjectName(u"hlay_output")
        self.label_output = QLabel(self.tab_setup)
        self.label_output.setObjectName(u"label_output")
        self.label_output.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.hlay_output.addWidget(self.label_output)

        self.output_folder = QLineEdit(self.tab_setup)
        self.output_folder.setObjectName(u"output_folder")

        self.hlay_output.addWidget(self.output_folder)

        self.ouput_folder_browse_button = QPushButton(self.tab_setup)
        self.ouput_folder_browse_button.setObjectName(u"ouput_folder_browse_button")

        self.hlay_output.addWidget(self.ouput_folder_browse_button)


        self.vlay_files.addLayout(self.hlay_output)

        self.vlay_plando = QVBoxLayout()
        self.vlay_plando.setObjectName(u"vlay_plando")
        self.hlay_plando_file = QHBoxLayout()
        self.hlay_plando_file.setObjectName(u"hlay_plando_file")
        self.label_for_apssr_file = QLabel(self.tab_setup)
        self.label_for_apssr_file.setObjectName(u"label_for_apssr_file")

        self.hlay_plando_file.addWidget(self.label_for_apssr_file)

        self.apssr_file = QLineEdit(self.tab_setup)
        self.apssr_file.setObjectName(u"apssr_file")

        self.hlay_plando_file.addWidget(self.apssr_file)

        self.apssr_file_browse = QPushButton(self.tab_setup)
        self.apssr_file_browse.setObjectName(u"apssr_file_browse")

        self.hlay_plando_file.addWidget(self.apssr_file_browse)


        self.vlay_plando.addLayout(self.hlay_plando_file)

        self.apssr_description_label = QLabel(self.tab_setup)
        self.apssr_description_label.setObjectName(u"apssr_description_label")
        self.apssr_description_label.setWordWrap(True)

        self.vlay_plando.addWidget(self.apssr_description_label)


        self.vlay_files.addLayout(self.vlay_plando)


        self.verticalLayout_27.addLayout(self.vlay_files)

        self.hlay_setup_options = QHBoxLayout()
        self.hlay_setup_options.setObjectName(u"hlay_setup_options")
        self.box_additional_files = QGroupBox(self.tab_setup)
        self.box_additional_files.setObjectName(u"box_additional_files")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.box_additional_files.sizePolicy().hasHeightForWidth())
        self.box_additional_files.setSizePolicy(sizePolicy2)
        self.box_additional_files.setFlat(False)
        self.verticalLayout_22 = QVBoxLayout(self.box_additional_files)
        self.verticalLayout_22.setObjectName(u"verticalLayout_22")
        self.vlay_additional_files = QVBoxLayout()
        self.vlay_additional_files.setObjectName(u"vlay_additional_files")
        self.option_no_spoiler_log = QCheckBox(self.box_additional_files)
        self.option_no_spoiler_log.setObjectName(u"option_no_spoiler_log")

        self.vlay_additional_files.addWidget(self.option_no_spoiler_log)

        self.option_json_spoiler = QCheckBox(self.box_additional_files)
        self.option_json_spoiler.setObjectName(u"option_json_spoiler")

        self.vlay_additional_files.addWidget(self.option_json_spoiler)

        self.option_out_placement_file = QCheckBox(self.box_additional_files)
        self.option_out_placement_file.setObjectName(u"option_out_placement_file")

        self.vlay_additional_files.addWidget(self.option_out_placement_file)

        self.vspace_additional_files = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.vlay_additional_files.addItem(self.vspace_additional_files)


        self.verticalLayout_22.addLayout(self.vlay_additional_files)


        self.hlay_setup_options.addWidget(self.box_additional_files)

        self.box_advanced = QGroupBox(self.tab_setup)
        self.box_advanced.setObjectName(u"box_advanced")
        sizePolicy2.setHeightForWidth(self.box_advanced.sizePolicy().hasHeightForWidth())
        self.box_advanced.setSizePolicy(sizePolicy2)
        self.verticalLayout_23 = QVBoxLayout(self.box_advanced)
        self.verticalLayout_23.setObjectName(u"verticalLayout_23")
        self.vlay_advanced = QVBoxLayout()
        self.vlay_advanced.setObjectName(u"vlay_advanced")
        self.option_dry_run = QCheckBox(self.box_advanced)
        self.option_dry_run.setObjectName(u"option_dry_run")

        self.vlay_advanced.addWidget(self.option_dry_run)

        self.option_print_messages = QCheckBox(self.box_advanced)
        self.option_print_messages.setObjectName(u"option_print_messages")

        self.vlay_advanced.addWidget(self.option_print_messages)

        self.option_emulator_mode = QCheckBox(self.box_advanced)
        self.option_emulator_mode.setObjectName(u"option_emulator_mode")

        self.vlay_advanced.addWidget(self.option_emulator_mode)

        self.vspace_advanced = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.vlay_advanced.addItem(self.vspace_advanced)


        self.verticalLayout_23.addLayout(self.vlay_advanced)


        self.hlay_setup_options.addWidget(self.box_advanced)

        self.box_cosmetics = QGroupBox(self.tab_setup)
        self.box_cosmetics.setObjectName(u"box_cosmetics")
        sizePolicy2.setHeightForWidth(self.box_cosmetics.sizePolicy().hasHeightForWidth())
        self.box_cosmetics.setSizePolicy(sizePolicy2)
        self.verticalLayout_24 = QVBoxLayout(self.box_cosmetics)
        self.verticalLayout_24.setObjectName(u"verticalLayout_24")
        self.vlay_cosmetics = QVBoxLayout()
        self.vlay_cosmetics.setObjectName(u"vlay_cosmetics")
        self.option_cryptic_location_hints = QCheckBox(self.box_cosmetics)
        self.option_cryptic_location_hints.setObjectName(u"option_cryptic_location_hints")

        self.vlay_cosmetics.addWidget(self.option_cryptic_location_hints)

        self.option_lightning_skyward_strike = QCheckBox(self.box_cosmetics)
        self.option_lightning_skyward_strike.setObjectName(u"option_lightning_skyward_strike")

        self.vlay_cosmetics.addWidget(self.option_lightning_skyward_strike)

        self.option_starry_skies = QCheckBox(self.box_cosmetics)
        self.option_starry_skies.setObjectName(u"option_starry_skies")

        self.vlay_cosmetics.addWidget(self.option_starry_skies)

        self.label_for_option_star_count = QLabel(self.box_cosmetics)
        self.label_for_option_star_count.setObjectName(u"label_for_option_star_count")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.label_for_option_star_count.sizePolicy().hasHeightForWidth())
        self.label_for_option_star_count.setSizePolicy(sizePolicy3)

        self.vlay_cosmetics.addWidget(self.label_for_option_star_count)

        self.option_star_count = QSpinBox(self.box_cosmetics)
        self.option_star_count.setObjectName(u"option_star_count")
        self.option_star_count.setEnabled(True)
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.option_star_count.sizePolicy().hasHeightForWidth())
        self.option_star_count.setSizePolicy(sizePolicy4)
        self.option_star_count.setMaximum(32767)
        self.option_star_count.setSingleStep(100)

        self.vlay_cosmetics.addWidget(self.option_star_count)

        self.label_for_option_interface = QLabel(self.box_cosmetics)
        self.label_for_option_interface.setObjectName(u"label_for_option_interface")

        self.vlay_cosmetics.addWidget(self.label_for_option_interface)

        self.option_interface = QComboBox(self.box_cosmetics)
        self.option_interface.setObjectName(u"option_interface")

        self.vlay_cosmetics.addWidget(self.option_interface)

        self.vspace_cosmetics = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.vlay_cosmetics.addItem(self.vspace_cosmetics)


        self.verticalLayout_24.addLayout(self.vlay_cosmetics)


        self.hlay_setup_options.addWidget(self.box_cosmetics)

        self.box_music_rando = QGroupBox(self.tab_setup)
        self.box_music_rando.setObjectName(u"box_music_rando")
        sizePolicy2.setHeightForWidth(self.box_music_rando.sizePolicy().hasHeightForWidth())
        self.box_music_rando.setSizePolicy(sizePolicy2)
        self.verticalLayout_25 = QVBoxLayout(self.box_music_rando)
        self.verticalLayout_25.setObjectName(u"verticalLayout_25")
        self.vlay_music_rando = QVBoxLayout()
        self.vlay_music_rando.setObjectName(u"vlay_music_rando")
        self.vlay_music_rando_option = QVBoxLayout()
        self.vlay_music_rando_option.setObjectName(u"vlay_music_rando_option")
        self.label_for_option_music_rando = QLabel(self.box_music_rando)
        self.label_for_option_music_rando.setObjectName(u"label_for_option_music_rando")

        self.vlay_music_rando_option.addWidget(self.label_for_option_music_rando)

        self.option_music_rando = QComboBox(self.box_music_rando)
        self.option_music_rando.setObjectName(u"option_music_rando")

        self.vlay_music_rando_option.addWidget(self.option_music_rando)


        self.vlay_music_rando.addLayout(self.vlay_music_rando_option)

        self.option_cutoff_gameover_music = QCheckBox(self.box_music_rando)
        self.option_cutoff_gameover_music.setObjectName(u"option_cutoff_gameover_music")

        self.vlay_music_rando.addWidget(self.option_cutoff_gameover_music)

        self.option_allow_custom_music = QCheckBox(self.box_music_rando)
        self.option_allow_custom_music.setObjectName(u"option_allow_custom_music")

        self.vlay_music_rando.addWidget(self.option_allow_custom_music)

        self.option_no_enemy_music = QCheckBox(self.box_music_rando)
        self.option_no_enemy_music.setObjectName(u"option_no_enemy_music")

        self.vlay_music_rando.addWidget(self.option_no_enemy_music)

        self.vspace_music_rando = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.vlay_music_rando.addItem(self.vspace_music_rando)


        self.verticalLayout_25.addLayout(self.vlay_music_rando)


        self.hlay_setup_options.addWidget(self.box_music_rando)

        self.box = QGroupBox(self.tab_setup)
        self.box.setObjectName(u"box")
        sizePolicy2.setHeightForWidth(self.box.sizePolicy().hasHeightForWidth())
        self.box.setSizePolicy(sizePolicy2)
        self.verticalLayout_28 = QVBoxLayout(self.box)
        self.verticalLayout_28.setObjectName(u"verticalLayout_28")
        self.vspace_10 = QSpacerItem(20, 342, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_28.addItem(self.vspace_10)


        self.hlay_setup_options.addWidget(self.box)


        self.verticalLayout_27.addLayout(self.hlay_setup_options)

        self.hlay_presets = QHBoxLayout()
        self.hlay_presets.setObjectName(u"hlay_presets")
        self.hspace_presets = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hlay_presets.addItem(self.hspace_presets)


        self.verticalLayout_27.addLayout(self.hlay_presets)

        self.tabWidget.addTab(self.tab_setup, "")
        self.tab_cosmetics = QWidget()
        self.tab_cosmetics.setObjectName(u"tab_cosmetics")
        self.verticalLayout_31 = QVBoxLayout(self.tab_cosmetics)
        self.verticalLayout_31.setObjectName(u"verticalLayout_31")
        self.hlay_cosmetics = QHBoxLayout()
        self.hlay_cosmetics.setObjectName(u"hlay_cosmetics")
        self.hlay_cosmetics.setContentsMargins(-1, -1, -1, 0)
        self.custom_model_settings = QVBoxLayout()
        self.custom_model_settings.setObjectName(u"custom_model_settings")
        self.hlay_type_options = QHBoxLayout()
        self.hlay_type_options.setObjectName(u"hlay_type_options")
        self.label_color_preset_select_label = QLabel(self.tab_cosmetics)
        self.label_color_preset_select_label.setObjectName(u"label_color_preset_select_label")

        self.hlay_type_options.addWidget(self.label_color_preset_select_label)

        self.option_model_type_select = QComboBox(self.tab_cosmetics)
        self.option_model_type_select.setObjectName(u"option_model_type_select")
        self.option_model_type_select.setEnabled(True)
        sizePolicy5 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy5.setHorizontalStretch(20)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.option_model_type_select.sizePolicy().hasHeightForWidth())
        self.option_model_type_select.setSizePolicy(sizePolicy5)

        self.hlay_type_options.addWidget(self.option_model_type_select)

        self.option_tunic_swap = QCheckBox(self.tab_cosmetics)
        self.option_tunic_swap.setObjectName(u"option_tunic_swap")
        self.option_tunic_swap.setEnabled(True)
        sizePolicy6 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy6.setHorizontalStretch(40)
        sizePolicy6.setVerticalStretch(0)
        sizePolicy6.setHeightForWidth(self.option_tunic_swap.sizePolicy().hasHeightForWidth())
        self.option_tunic_swap.setSizePolicy(sizePolicy6)

        self.hlay_type_options.addWidget(self.option_tunic_swap)

        self.hspace_type_options = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hlay_type_options.addItem(self.hspace_type_options)


        self.custom_model_settings.addLayout(self.hlay_type_options)

        self.hlay_pack_options = QHBoxLayout()
        self.hlay_pack_options.setObjectName(u"hlay_pack_options")
        self.label_player_model_select = QLabel(self.tab_cosmetics)
        self.label_player_model_select.setObjectName(u"label_player_model_select")

        self.hlay_pack_options.addWidget(self.label_player_model_select)

        self.option_model_pack_select = QComboBox(self.tab_cosmetics)
        self.option_model_pack_select.setObjectName(u"option_model_pack_select")
        sizePolicy7 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy7.setHorizontalStretch(20)
        sizePolicy7.setVerticalStretch(0)
        sizePolicy7.setHeightForWidth(self.option_model_pack_select.sizePolicy().hasHeightForWidth())
        self.option_model_pack_select.setSizePolicy(sizePolicy7)

        self.hlay_pack_options.addWidget(self.option_model_pack_select)

        self.button_randomize_all_colors = QPushButton(self.tab_cosmetics)
        self.button_randomize_all_colors.setObjectName(u"button_randomize_all_colors")
        sizePolicy7.setHeightForWidth(self.button_randomize_all_colors.sizePolicy().hasHeightForWidth())
        self.button_randomize_all_colors.setSizePolicy(sizePolicy7)

        self.hlay_pack_options.addWidget(self.button_randomize_all_colors)

        self.button_reset_all_colors = QPushButton(self.tab_cosmetics)
        self.button_reset_all_colors.setObjectName(u"button_reset_all_colors")
        sizePolicy7.setHeightForWidth(self.button_reset_all_colors.sizePolicy().hasHeightForWidth())
        self.button_reset_all_colors.setSizePolicy(sizePolicy7)

        self.hlay_pack_options.addWidget(self.button_reset_all_colors)

        self.hspace_pack_options = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hlay_pack_options.addItem(self.hspace_pack_options)


        self.custom_model_settings.addLayout(self.hlay_pack_options)


        self.hlay_cosmetics.addLayout(self.custom_model_settings)

        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(-1, -1, -1, 0)
        self.button_save_color_preset = QPushButton(self.tab_cosmetics)
        self.button_save_color_preset.setObjectName(u"button_save_color_preset")

        self.gridLayout.addWidget(self.button_save_color_preset, 1, 2, 1, 1)

        self.button_load_color_preset = QPushButton(self.tab_cosmetics)
        self.button_load_color_preset.setObjectName(u"button_load_color_preset")

        self.gridLayout.addWidget(self.button_load_color_preset, 1, 1, 1, 1)

        self.button_delete_color_preset = QPushButton(self.tab_cosmetics)
        self.button_delete_color_preset.setObjectName(u"button_delete_color_preset")

        self.gridLayout.addWidget(self.button_delete_color_preset, 1, 3, 1, 1)

        self.button_color_imports = QPushButton(self.tab_cosmetics)
        self.button_color_imports.setObjectName(u"button_color_imports")

        self.gridLayout.addWidget(self.button_color_imports, 1, 0, 1, 1)

        self.label_for_color_presets = QLabel(self.tab_cosmetics)
        self.label_for_color_presets.setObjectName(u"label_for_color_presets")
        sizePolicy8 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy8.setHorizontalStretch(20)
        sizePolicy8.setVerticalStretch(0)
        sizePolicy8.setHeightForWidth(self.label_for_color_presets.sizePolicy().hasHeightForWidth())
        self.label_for_color_presets.setSizePolicy(sizePolicy8)
        self.label_for_color_presets.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout.addWidget(self.label_for_color_presets, 0, 0, 1, 1)

        self.color_presets_list = QComboBox(self.tab_cosmetics)
        self.color_presets_list.setObjectName(u"color_presets_list")
        sizePolicy5.setHeightForWidth(self.color_presets_list.sizePolicy().hasHeightForWidth())
        self.color_presets_list.setSizePolicy(sizePolicy5)

        self.gridLayout.addWidget(self.color_presets_list, 0, 1, 1, 3)


        self.hlay_cosmetics.addLayout(self.gridLayout)


        self.verticalLayout_31.addLayout(self.hlay_cosmetics)

        self.hlay_colors_and_preview = QHBoxLayout()
        self.hlay_colors_and_preview.setObjectName(u"hlay_colors_and_preview")
        self.scroll_area_colors = QScrollArea(self.tab_cosmetics)
        self.scroll_area_colors.setObjectName(u"scroll_area_colors")
        self.scroll_area_colors.setContextMenuPolicy(Qt.ContextMenuPolicy.PreventContextMenu)
        self.scroll_area_colors.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area_colors.setFrameShadow(QFrame.Shadow.Plain)
        self.scroll_area_colors.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area_colors.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area_colors.setWidgetResizable(True)
        self.scroll_area_colors.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self.scroll_area_widget_contents_colors = QWidget()
        self.scroll_area_widget_contents_colors.setObjectName(u"scroll_area_widget_contents_colors")
        self.scroll_area_widget_contents_colors.setGeometry(QRect(0, 0, 98, 46))
        self.verticalLayout_34 = QVBoxLayout(self.scroll_area_widget_contents_colors)
        self.verticalLayout_34.setObjectName(u"verticalLayout_34")
        self.vlay_texture_colors = QVBoxLayout()
        self.vlay_texture_colors.setObjectName(u"vlay_texture_colors")
        self.vspace_colors = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.vlay_texture_colors.addItem(self.vspace_colors)

        self.hspace_colors = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.vlay_texture_colors.addItem(self.hspace_colors)


        self.verticalLayout_34.addLayout(self.vlay_texture_colors)

        self.scroll_area_colors.setWidget(self.scroll_area_widget_contents_colors)

        self.hlay_colors_and_preview.addWidget(self.scroll_area_colors)

        self.vlay_preview = QVBoxLayout()
        self.vlay_preview.setObjectName(u"vlay_preview")
        self.hlay_preview = QHBoxLayout()
        self.hlay_preview.setObjectName(u"hlay_preview")
        self.label_preview_image = QLabel(self.tab_cosmetics)
        self.label_preview_image.setObjectName(u"label_preview_image")
        sizePolicy1.setHeightForWidth(self.label_preview_image.sizePolicy().hasHeightForWidth())
        self.label_preview_image.setSizePolicy(sizePolicy1)
        self.label_preview_image.setScaledContents(False)
        self.label_preview_image.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.hlay_preview.addWidget(self.label_preview_image)


        self.vlay_preview.addLayout(self.hlay_preview)


        self.hlay_colors_and_preview.addLayout(self.vlay_preview)


        self.verticalLayout_31.addLayout(self.hlay_colors_and_preview)

        self.tabWidget.addTab(self.tab_cosmetics, "")
        self.tab_accessibility = QWidget()
        self.tab_accessibility.setObjectName(u"tab_accessibility")
        self.tab_accessibility.setEnabled(True)
        self.horizontalLayout_3 = QHBoxLayout(self.tab_accessibility)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.box_theme = QGroupBox(self.tab_accessibility)
        self.box_theme.setObjectName(u"box_theme")
        sizePolicy2.setHeightForWidth(self.box_theme.sizePolicy().hasHeightForWidth())
        self.box_theme.setSizePolicy(sizePolicy2)
        self.verticalLayout_3 = QVBoxLayout(self.box_theme)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.vlay_theme = QVBoxLayout()
        self.vlay_theme.setObjectName(u"vlay_theme")
        self.theme_mode_label = QLabel(self.box_theme)
        self.theme_mode_label.setObjectName(u"theme_mode_label")

        self.vlay_theme.addWidget(self.theme_mode_label)

        self.option_theme_mode = QComboBox(self.box_theme)
        self.option_theme_mode.setObjectName(u"option_theme_mode")

        self.vlay_theme.addWidget(self.option_theme_mode)

        self.theme_presets_label = QLabel(self.box_theme)
        self.theme_presets_label.setObjectName(u"theme_presets_label")

        self.vlay_theme.addWidget(self.theme_presets_label)

        self.option_theme_presets = QComboBox(self.box_theme)
        self.option_theme_presets.setObjectName(u"option_theme_presets")

        self.vlay_theme.addWidget(self.option_theme_presets)

        self.option_use_custom_theme = QCheckBox(self.box_theme)
        self.option_use_custom_theme.setObjectName(u"option_use_custom_theme")

        self.vlay_theme.addWidget(self.option_use_custom_theme)

        self.custom_theme_button = QPushButton(self.box_theme)
        self.custom_theme_button.setObjectName(u"custom_theme_button")
        self.custom_theme_button.setEnabled(False)

        self.vlay_theme.addWidget(self.custom_theme_button)

        self.option_use_sharp_corners = QCheckBox(self.box_theme)
        self.option_use_sharp_corners.setObjectName(u"option_use_sharp_corners")

        self.vlay_theme.addWidget(self.option_use_sharp_corners)

        self.vspace_theme = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.vlay_theme.addItem(self.vspace_theme)


        self.verticalLayout_3.addLayout(self.vlay_theme)


        self.horizontalLayout_3.addWidget(self.box_theme)

        self.box_font = QGroupBox(self.tab_accessibility)
        self.box_font.setObjectName(u"box_font")
        sizePolicy2.setHeightForWidth(self.box_font.sizePolicy().hasHeightForWidth())
        self.box_font.setSizePolicy(sizePolicy2)
        self.verticalLayout_2 = QVBoxLayout(self.box_font)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.vlay_font = QVBoxLayout()
        self.vlay_font.setObjectName(u"vlay_font")
        self.label_for_option_font_family = QLabel(self.box_font)
        self.label_for_option_font_family.setObjectName(u"label_for_option_font_family")
        self.label_for_option_font_family.setFont(font)

        self.vlay_font.addWidget(self.label_for_option_font_family)

        self.option_font_family = QFontComboBox(self.box_font)
        self.option_font_family.setObjectName(u"option_font_family")
        sizePolicy9 = QSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        sizePolicy9.setHorizontalStretch(0)
        sizePolicy9.setVerticalStretch(0)
        sizePolicy9.setHeightForWidth(self.option_font_family.sizePolicy().hasHeightForWidth())
        self.option_font_family.setSizePolicy(sizePolicy9)
        self.option_font_family.setEditable(False)
        self.option_font_family.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContentsOnFirstShow)
        self.option_font_family.setWritingSystem(QFontDatabase.WritingSystem.Any)
        self.option_font_family.setFontFilters(QFontComboBox.FontFilter.ScalableFonts)
        font1 = QFont()
        font1.setFamilies([u"Arial"])
        font1.setPointSize(10)
        self.option_font_family.setCurrentFont(font1)

        self.vlay_font.addWidget(self.option_font_family)

        self.label_for_option_font_size = QLabel(self.box_font)
        self.label_for_option_font_size.setObjectName(u"label_for_option_font_size")
        sizePolicy.setHeightForWidth(self.label_for_option_font_size.sizePolicy().hasHeightForWidth())
        self.label_for_option_font_size.setSizePolicy(sizePolicy)

        self.vlay_font.addWidget(self.label_for_option_font_size)

        self.option_font_size = QSpinBox(self.box_font)
        self.option_font_size.setObjectName(u"option_font_size")
        sizePolicy4.setHeightForWidth(self.option_font_size.sizePolicy().hasHeightForWidth())
        self.option_font_size.setSizePolicy(sizePolicy4)

        self.vlay_font.addWidget(self.option_font_size)

        self.reset_font_button = QPushButton(self.box_font)
        self.reset_font_button.setObjectName(u"reset_font_button")
        sizePolicy10 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy10.setHorizontalStretch(0)
        sizePolicy10.setVerticalStretch(0)
        sizePolicy10.setHeightForWidth(self.reset_font_button.sizePolicy().hasHeightForWidth())
        self.reset_font_button.setSizePolicy(sizePolicy10)

        self.vlay_font.addWidget(self.reset_font_button)

        self.vspace_font = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.vlay_font.addItem(self.vspace_font)


        self.verticalLayout_2.addLayout(self.vlay_font)


        self.horizontalLayout_3.addWidget(self.box_font)

        self.box_1 = QGroupBox(self.tab_accessibility)
        self.box_1.setObjectName(u"box_1")
        self.box_1.setEnabled(True)
        sizePolicy2.setHeightForWidth(self.box_1.sizePolicy().hasHeightForWidth())
        self.box_1.setSizePolicy(sizePolicy2)
        self.box_1.setFlat(False)
        self.verticalLayout_9 = QVBoxLayout(self.box_1)
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.vspace = QSpacerItem(20, 533, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_9.addItem(self.vspace)


        self.horizontalLayout_3.addWidget(self.box_1)

        self.box_2 = QGroupBox(self.tab_accessibility)
        self.box_2.setObjectName(u"box_2")
        self.box_2.setEnabled(True)
        sizePolicy2.setHeightForWidth(self.box_2.sizePolicy().hasHeightForWidth())
        self.box_2.setSizePolicy(sizePolicy2)
        self.box_2.setFlat(False)
        self.verticalLayout_10 = QVBoxLayout(self.box_2)
        self.verticalLayout_10.setObjectName(u"verticalLayout_10")
        self.vspace_2 = QSpacerItem(20, 533, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_10.addItem(self.vspace_2)


        self.horizontalLayout_3.addWidget(self.box_2)

        self.box_3 = QGroupBox(self.tab_accessibility)
        self.box_3.setObjectName(u"box_3")
        self.box_3.setEnabled(True)
        sizePolicy2.setHeightForWidth(self.box_3.sizePolicy().hasHeightForWidth())
        self.box_3.setSizePolicy(sizePolicy2)
        self.box_3.setFlat(False)
        self.verticalLayout_11 = QVBoxLayout(self.box_3)
        self.verticalLayout_11.setObjectName(u"verticalLayout_11")
        self.vspace_3 = QSpacerItem(20, 533, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_11.addItem(self.vspace_3)


        self.horizontalLayout_3.addWidget(self.box_3)

        self.tabWidget.addTab(self.tab_accessibility, "")

        self.verticalLayout.addWidget(self.tabWidget)

        self.option_description = QLabel(self.centralwidget)
        self.option_description.setObjectName(u"option_description")
        self.option_description.setEnabled(True)
        sizePolicy11 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        sizePolicy11.setHorizontalStretch(0)
        sizePolicy11.setVerticalStretch(0)
        sizePolicy11.setHeightForWidth(self.option_description.sizePolicy().hasHeightForWidth())
        self.option_description.setSizePolicy(sizePolicy11)
        self.option_description.setMinimumSize(QSize(0, 48))
        self.option_description.setStyleSheet(u"")
        self.option_description.setTextFormat(Qt.TextFormat.MarkdownText)
        self.option_description.setWordWrap(True)

        self.verticalLayout.addWidget(self.option_description)

        self.vlay_bottom_controls = QVBoxLayout()
        self.vlay_bottom_controls.setObjectName(u"vlay_bottom_controls")
        self.hlay_settings_string = QHBoxLayout()
        self.hlay_settings_string.setObjectName(u"hlay_settings_string")
        self.label_for_settings_string = QLabel(self.centralwidget)
        self.label_for_settings_string.setObjectName(u"label_for_settings_string")

        self.hlay_settings_string.addWidget(self.label_for_settings_string)

        self.settings_string = QLineEdit(self.centralwidget)
        self.settings_string.setObjectName(u"settings_string")
        self.settings_string.setReadOnly(True)

        self.hlay_settings_string.addWidget(self.settings_string)


        self.vlay_bottom_controls.addLayout(self.hlay_settings_string)

        self.hlay_button_row = QHBoxLayout()
        self.hlay_button_row.setObjectName(u"hlay_button_row")
        self.randomize_button = QPushButton(self.centralwidget)
        self.randomize_button.setObjectName(u"randomize_button")

        self.hlay_button_row.addWidget(self.randomize_button)


        self.vlay_bottom_controls.addLayout(self.hlay_button_row)


        self.verticalLayout.addLayout(self.vlay_bottom_controls)

        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)

        self.tabWidget.setCurrentIndex(0)
        self.option_model_pack_select.setCurrentIndex(-1)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Skyward Sword Randomizer", None))
#if QT_CONFIG(tooltip)
        self.tabWidget.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.label_output.setText(QCoreApplication.translate("MainWindow", u"Output Folder", None))
        self.ouput_folder_browse_button.setText(QCoreApplication.translate("MainWindow", u"Browse", None))
        self.label_for_apssr_file.setText(QCoreApplication.translate("MainWindow", u"Archipelago APSSR File", None))
        self.apssr_file_browse.setText(QCoreApplication.translate("MainWindow", u"Browse", None))
        self.apssr_description_label.setText(QCoreApplication.translate("MainWindow", u"The Archipelago APSSR file should be a personal encoded file (extension *.apssr) that is given to you by the Archipelago multiworld host. If you have not received one, please ask the host to send it to you. This file contains this Skyward Sword world's options and locations used for randomization.", None))
        self.box_additional_files.setTitle(QCoreApplication.translate("MainWindow", u"Additional File Generation", None))
        self.option_no_spoiler_log.setText(QCoreApplication.translate("MainWindow", u"No Spoiler Log", None))
        self.option_json_spoiler.setText(QCoreApplication.translate("MainWindow", u"Generate JSON Spoiler Log", None))
        self.option_out_placement_file.setText(QCoreApplication.translate("MainWindow", u"Generate Placement File", None))
        self.box_advanced.setTitle(QCoreApplication.translate("MainWindow", u"Advanced Options", None))
        self.option_dry_run.setText(QCoreApplication.translate("MainWindow", u"Dry Run", None))
        self.option_print_messages.setText(QCoreApplication.translate("MainWindow", u"Print Client Messages", None))
        self.option_emulator_mode.setText(QCoreApplication.translate("MainWindow", u"Emulator Mode", None))
        self.box_cosmetics.setTitle(QCoreApplication.translate("MainWindow", u"Cosmetics", None))
        self.option_cryptic_location_hints.setText(QCoreApplication.translate("MainWindow", u"Cryptic Location Hints", None))
        self.option_lightning_skyward_strike.setText(QCoreApplication.translate("MainWindow", u"Lightning Skyward Strike", None))
        self.option_starry_skies.setText(QCoreApplication.translate("MainWindow", u"Starry Skies", None))
        self.label_for_option_star_count.setText(QCoreApplication.translate("MainWindow", u"Number of stars", None))
        self.label_for_option_interface.setText(QCoreApplication.translate("MainWindow", u"Starting Interface", None))
        self.box_music_rando.setTitle(QCoreApplication.translate("MainWindow", u"Randomize Music", None))
        self.label_for_option_music_rando.setText(QCoreApplication.translate("MainWindow", u"Randomize Music", None))
        self.option_cutoff_gameover_music.setText(QCoreApplication.translate("MainWindow", u"Cutoff Game Over Music", None))
        self.option_allow_custom_music.setText(QCoreApplication.translate("MainWindow", u"Allow Custom Music", None))
        self.option_no_enemy_music.setText(QCoreApplication.translate("MainWindow", u"Remove Enemy Music", None))
        self.box.setTitle("")
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_setup), QCoreApplication.translate("MainWindow", u"Setup", None))
        self.label_color_preset_select_label.setText(QCoreApplication.translate("MainWindow", u"Type", None))
        self.option_tunic_swap.setText(QCoreApplication.translate("MainWindow", u"Tunic Swap", None))
        self.label_player_model_select.setText(QCoreApplication.translate("MainWindow", u"Pack", None))
        self.button_randomize_all_colors.setText(QCoreApplication.translate("MainWindow", u"Randomize All Colors", None))
        self.button_reset_all_colors.setText(QCoreApplication.translate("MainWindow", u"Reset All Colors", None))
        self.button_save_color_preset.setText(QCoreApplication.translate("MainWindow", u"Save", None))
        self.button_load_color_preset.setText(QCoreApplication.translate("MainWindow", u"Load", None))
        self.button_delete_color_preset.setText(QCoreApplication.translate("MainWindow", u"Delete", None))
        self.button_color_imports.setText(QCoreApplication.translate("MainWindow", u"Import/Export", None))
        self.label_for_color_presets.setText(QCoreApplication.translate("MainWindow", u"Color Presets", None))
        self.label_preview_image.setText("")
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_cosmetics), QCoreApplication.translate("MainWindow", u"Cosmetics", None))
        self.box_theme.setTitle(QCoreApplication.translate("MainWindow", u"Theming", None))
        self.theme_mode_label.setText(QCoreApplication.translate("MainWindow", u"Theme Mode", None))
        self.option_theme_mode.setCurrentText("")
        self.theme_presets_label.setText(QCoreApplication.translate("MainWindow", u"Theme Presets", None))
        self.option_theme_presets.setCurrentText("")
        self.option_use_custom_theme.setText(QCoreApplication.translate("MainWindow", u"Use Custom Theme", None))
        self.custom_theme_button.setText(QCoreApplication.translate("MainWindow", u"Customize Theme", None))
        self.option_use_sharp_corners.setText(QCoreApplication.translate("MainWindow", u"Sharp Corners", None))
        self.box_font.setTitle(QCoreApplication.translate("MainWindow", u"Fonts", None))
        self.label_for_option_font_family.setText(QCoreApplication.translate("MainWindow", u"Font Family", None))
        self.option_font_family.setCurrentText(QCoreApplication.translate("MainWindow", u"Arial", None))
        self.option_font_family.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Select Font Family", None))
        self.label_for_option_font_size.setText(QCoreApplication.translate("MainWindow", u"Font Size", None))
        self.reset_font_button.setText(QCoreApplication.translate("MainWindow", u"Reset", None))
        self.box_1.setTitle("")
        self.box_2.setTitle("")
        self.box_3.setTitle("")
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_accessibility), QCoreApplication.translate("MainWindow", u"Accessibility", None))
        self.option_description.setText("")
        self.label_for_settings_string.setText(QCoreApplication.translate("MainWindow", u"Last Generated Settings String:", None))
        self.randomize_button.setText(QCoreApplication.translate("MainWindow", u"Randomize", None))
    # retranslateUi

