from distutils.command.check import check

from shiboken2 import wrapInstance

import os
import maya.cmds as cm
# import pymel.core as pm
import maya.OpenMaya as OM
import maya.OpenMayaUI as OMUI

from PySide2 import QtWidgets, QtCore, QtGui
from maya.mel import eval


# import sys


class QHLine(QtWidgets.QFrame):

    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(self.HLine)
        self.setFrameShadow(self.Sunken)


class QVLine(QtWidgets.QFrame):

    def __init__(self):
        super(QVLine, self).__init__()
        self.setFrameShape(self.VLine)
        self.setFrameShadow(self.Sunken)


class QHLineName(QtWidgets.QGridLayout):

    def __init__(self, name):
        super(QHLineName, self).__init__()
        name_lb = QtWidgets.QLabel(name)
        name_lb.setAlignment(QtCore.Qt.AlignCenter)
        name_lb.setStyleSheet("font: italic 9pt;" "color: azure;")
        self.addWidget(name_lb, 0, 0, 1, 1)
        self.addWidget(QHLine(), 0, 1, 1, 2)


# noinspection PyAttributeOutsideInit
class M2Bake(QtWidgets.QWidget):

    def __init__(self):
        super(M2Bake, self).__init__()

        self.create_widgets()
        self.create_layouts()
        self.create_connections()

    def create_widgets(self):
        self.namespace_lb = QtWidgets.QLabel("Name space:")
        self.namespace_le = QtWidgets.QLineEdit()
        self.namespace_btn = QtWidgets.QPushButton("Assign")

        self.fk_to_ik_arm_right_cb = QtWidgets.QCheckBox("Right Arm")
        self.fk_to_ik_arm_left_cb = QtWidgets.QCheckBox("Left Arm")
        self.fk_to_ik_leg_right_cb = QtWidgets.QCheckBox("Right Leg")
        self.fk_to_ik_leg_left_cb = QtWidgets.QCheckBox("Left Leg")
        self.fk_to_ik_bake_btn = QtWidgets.QPushButton("Bake FK to IK")

        self.ik_to_fk_arm_right_cb = QtWidgets.QCheckBox("Right Arm")
        self.ik_to_fk_arm_left_cb = QtWidgets.QCheckBox("Left Arm")
        self.ik_to_fk_leg_right_cb = QtWidgets.QCheckBox("Right Leg")
        self.ik_to_fk_leg_left_cb = QtWidgets.QCheckBox("Left Leg")
        self.ik_to_fk_bake_btn = QtWidgets.QPushButton("Bake IK to FK")

    def create_layouts(self):
        first_layout = QtWidgets.QHBoxLayout()
        first_layout.addWidget(self.namespace_lb)
        first_layout.addWidget(self.namespace_le)
        first_layout.addWidget(self.namespace_btn)

        second_layout = QtWidgets.QHBoxLayout()
        second_layout.addWidget(self.fk_to_ik_arm_right_cb)
        second_layout.addWidget(self.fk_to_ik_arm_left_cb)
        second_layout.addWidget(self.fk_to_ik_leg_right_cb)
        second_layout.addWidget(self.fk_to_ik_leg_left_cb)
        second_layout.addWidget(self.fk_to_ik_bake_btn)

        third_layout = QtWidgets.QHBoxLayout()
        third_layout.addWidget(self.ik_to_fk_arm_right_cb)
        third_layout.addWidget(self.ik_to_fk_arm_left_cb)
        third_layout.addWidget(self.ik_to_fk_leg_right_cb)
        third_layout.addWidget(self.ik_to_fk_leg_left_cb)
        third_layout.addWidget(self.ik_to_fk_bake_btn)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addLayout(first_layout)
        main_layout.addLayout(QHLineName("FK to IK"))
        main_layout.addLayout(second_layout)
        main_layout.addLayout(QHLineName("IK to FK"))
        main_layout.addLayout(third_layout)

    def create_connections(self):
        self.namespace_btn.clicked.connect(self.namespace_assign)
        self.fk_to_ik_bake_btn.clicked.connect(self.bake_fk_to_ik)
        self.ik_to_fk_bake_btn.clicked.connect(self.bake_ik_to_fk)

    def namespace_assign(self):
        try:
            current_selection = cm.ls(sl=True)
            if len(current_selection) == 1:
                name_object = current_selection[0]

                namespace = name_object.rpartition(":")[0]

                self.namespace_le.setText(namespace)
            else:
                OM.MGlobal_displayError("Please chose only one object to get the current namespace")

        except TypeError as e:
            OM.MGlobal_displayError(f"There was error at {e}")

    def bake_fk_to_ik(self):
        namespace = self.namespace_le.text()
        cm.currentTime(-1)

        list_fk_ik_control_switch_name = ["armGlobalRGT_ctrl", "armGlobalLFT_ctrl", "legGlobalRGT_ctrl",
                                          "legGlobalLFT_ctrl"]

        # set all control to FK
        for i in list_fk_ik_control_switch_name:
            cm.setAttr(f"{namespace}:{i}.fk2ik", 0)

        list_joint = ["jnt_r_armWrist", "jnt_l_armWrist", "jnt_r_arm_lowerTwist_000", "jnt_l_arm_lowerTwist_000",
                      "jnt_r_arm_upperTwist_000", "jnt_l_arm_upperTwist_000", "jnt_r_legWrist", "jnt_l_legWrist",
                      "jnt_r_leg_lowerTwist_000", "jnt_l_leg_lowerTwist_000", "jnt_r_leg_upperTwist_000",
                      "jnt_l_leg_upperTwist_000"]
        list_loc_bake = []
        list_constraint_bake = []

        for joint_bake in list_joint:
            loc = cm.spaceLocator(name=f"{joint_bake}_loc")[0]
            list_loc_bake.append(loc)
            cont = cm.parentConstraint(f"{namespace}:{joint_bake}", loc, mo=False)[0]
            list_constraint_bake.append(cont)

        min_time = int(-1)
        max_time = cm.playbackOptions(q=True, max=True)
        cm.select(list_loc_bake)

        eval(
            'bakeResults -simulation true -t "{0}:{1}" -sampleBy 1 -oversamplingRate 1 '
            '-disableImplicitControl true -preserveOutsideKeys true -sparseAnimCurveBake false '
            '-removeBakedAttributeFromLayer false -removeBakedAnimFromLayer false -bakeOnOverrideLayer '
            'false -minimizeRotation true -controlPoints false -shape false;'.format(
                min_time, max_time))

        cm.delete(list_constraint_bake)

        for i in list_fk_ik_control_switch_name:
            cm.setAttr(f"{namespace}:{i}.fk2ik", 1)

        list_ik_control = []

        for loc in list_loc_bake:
            # Right Arm
            if "jnt_r_armWrist" in str(loc):
                if self.fk_to_ik_arm_right_cb.isChecked():
                    cm.parentConstraint(loc, f"{namespace}:armIkRGT_ctrl", mo=True)
                    list_ik_control.append(f"{namespace}:armIkRGT_ctrl")
            if "jnt_r_arm_lowerTwist_000" in str(loc):
                if self.fk_to_ik_arm_right_cb.isChecked():
                    cm.parentConstraint(loc, f"{namespace}:armPoleRGT_ctrl", skipRotate=["x", "y", "z"])
                    list_ik_control.append(f"{namespace}:armPoleRGT_ctrl")

            # Left Arm
            if "jnt_l_armWrist" in str(loc):
                if self.fk_to_ik_arm_left_cb.isChecked():
                    cm.parentConstraint(loc, f"{namespace}:armIkLFT_ctrl", mo=True)
                    list_ik_control.append(f"{namespace}:armIkLFT_ctrl")
            if "jnt_l_arm_lowerTwist_000" in str(loc):
                if self.fk_to_ik_arm_left_cb.isChecked():
                    cm.parentConstraint(loc, f"{namespace}:armPoleLFT_ctrl", skipRotate=["x", "y", "z"])
                    list_ik_control.append(f"{namespace}:armPoleLFT_ctrl")

            # Right Leg
            if "jnt_r_legWrist" in str(loc):
                if self.fk_to_ik_leg_right_cb.isChecked():
                    cm.parentConstraint(loc, f"{namespace}:legIkRGT_ctrl", mo=True)
                    list_ik_control.append(f"{namespace}:legIkRGT_ctrl")
            if "jnt_r_leg_lowerTwist_000" in str(loc):
                if self.fk_to_ik_leg_right_cb.isChecked():
                    cm.parentConstraint(loc, f"{namespace}:legPoleRGT_ctrl", skipRotate=["x", "y", "z"])
                    list_ik_control.append(f"{namespace}:legPoleRGT_ctrl")

            # Left Leg
            if "jnt_l_legWrist" in str(loc):
                if self.fk_to_ik_leg_left_cb.isChecked():
                    cm.parentConstraint(loc, f"{namespace}:legIkLFT_ctrl", mo=True)
                    list_ik_control.append(f"{namespace}:legIkLFT_ctrl")
            if "jnt_l_leg_lowerTwist_000" in str(loc):
                if self.fk_to_ik_leg_left_cb.isChecked():
                    cm.parentConstraint(loc, f"{namespace}:legPoleLFT_ctrl", skipRotate=["x", "y", "z"])
                    list_ik_control.append(f"{namespace}:legPoleLFT_ctrl")

        cm.select(list_ik_control)

        eval(
            'bakeResults -simulation true -t "{0}:{1}" -sampleBy 1 -oversamplingRate 1 '
            '-disableImplicitControl true -preserveOutsideKeys true -sparseAnimCurveBake false '
            '-removeBakedAttributeFromLayer false -removeBakedAnimFromLayer false -bakeOnOverrideLayer '
            'false -minimizeRotation true -controlPoints false -shape false;'.format(
                min_time, max_time))

        cm.delete(list_loc_bake)

    def bake_ik_to_fk(self):
        namespace = self.namespace_le.text()
        cm.currentTime(-1)

        list_fk_ik_control_switch_name = ["armGlobalRGT_ctrl", "armGlobalLFT_ctrl", "legGlobalRGT_ctrl",
                                          "legGlobalLFT_ctrl"]

        # set all control to FK
        for i in list_fk_ik_control_switch_name:
            cm.setAttr(f"{namespace}:{i}.fk2ik", 1)

        list_joint = ["jnt_r_armWrist", "jnt_l_armWrist", "jnt_r_arm_lowerTwist_000", "jnt_l_arm_lowerTwist_000",
                      "jnt_r_arm_upperTwist_000", "jnt_l_arm_upperTwist_000", "jnt_r_legWrist", "jnt_l_legWrist",
                      "jnt_r_leg_lowerTwist_000", "jnt_l_leg_lowerTwist_000", "jnt_r_leg_upperTwist_000",
                      "jnt_l_leg_upperTwist_000"]
        list_loc_bake = []
        list_constraint_bake = []

        for joint_bake in list_joint:
            loc = cm.spaceLocator(name=f"{joint_bake}_loc")[0]
            list_loc_bake.append(loc)
            cont = cm.parentConstraint(f"{namespace}:{joint_bake}", loc, mo=False)[0]
            list_constraint_bake.append(cont)

        min_time = int(-1)
        max_time = cm.playbackOptions(q=True, max=True)
        cm.select(list_loc_bake)

        eval(
            'bakeResults -simulation true -t "{0}:{1}" -sampleBy 1 -oversamplingRate 1 '
            '-disableImplicitControl true -preserveOutsideKeys true -sparseAnimCurveBake false '
            '-removeBakedAttributeFromLayer false -removeBakedAnimFromLayer false -bakeOnOverrideLayer '
            'false -minimizeRotation true -controlPoints false -shape false;'.format(
                min_time, max_time))

        cm.delete(list_constraint_bake)

        for i in list_fk_ik_control_switch_name:
            cm.setAttr(f"{namespace}:{i}.fk2ik", 0)

        list_fk_control = []

        for loc in list_loc_bake:
            # Right Arm
            if "jnt_r_armWrist" in str(loc):
                if self.ik_to_fk_arm_right_cb.isChecked():
                    cm.parentConstraint(loc, f"{namespace}:armWristRGT_ctrl", mo=True)
                    list_fk_control.append(f"{namespace}:armWristRGT_ctrl")
            if "jnt_r_arm_lowerTwist_000" in str(loc):
                if self.ik_to_fk_arm_right_cb.isChecked():
                    cm.parentConstraint(loc, f"{namespace}:armElbowRGT_ctrl", mo=True)
                    list_fk_control.append(f"{namespace}:armElbowRGT_ctrl")
            if "jnt_r_arm_upperTwist_000" in str(loc):
                if self.ik_to_fk_arm_right_cb.isChecked():
                    cm.parentConstraint(loc, f"{namespace}:armUpperRGT_ctrl", mo=True,
                                        skipTranslate=["x", "y", "z"])
                    list_fk_control.append(f"{namespace}:armUpperRGT_ctrl")

            # Left Arm
            if "jnt_l_armWrist" in str(loc):
                if self.ik_to_fk_arm_left_cb.isChecked():
                    cm.parentConstraint(loc, f"{namespace}:armWristLFT_ctrl", mo=True)
                    list_fk_control.append(f"{namespace}:armWristLFT_ctrl")
            if "jnt_l_arm_lowerTwist_000" in str(loc):
                if self.ik_to_fk_arm_left_cb.isChecked():
                    cm.parentConstraint(loc, f"{namespace}:armElbowLFT_ctrl", mo=True)
                    list_fk_control.append(f"{namespace}:armElbowLFT_ctrl")
            if "jnt_l_arm_upperTwist_000" in str(loc):
                if self.ik_to_fk_arm_left_cb.isChecked():
                    cm.parentConstraint(loc, f"{namespace}:armUpperLFT_ctrl", mo=True,
                                        skipTranslate=["x", "y", "z"])
                    list_fk_control.append(f"{namespace}:armUpperLFT_ctrl")

            # Right Leg
            if "jnt_r_legWrist" in str(loc):
                if self.ik_to_fk_leg_right_cb.isChecked():
                    cm.parentConstraint(loc, f"{namespace}:legAnkleRGT_ctrl", mo=True)
                    list_fk_control.append(f"{namespace}:legAnkleRGT_ctrl")
            if "jnt_r_leg_lowerTwist_000" in str(loc):
                if self.ik_to_fk_leg_right_cb.isChecked():
                    cm.parentConstraint(loc, f"{namespace}:legKneeRGT_ctrl", mo=True)
                    list_fk_control.append(f"{namespace}:legKneeRGT_ctrl")
            if "jnt_r_leg_upperTwist_000" in str(loc):
                if self.ik_to_fk_leg_right_cb.isChecked():
                    cm.parentConstraint(loc, f"{namespace}:legUpperRGT_ctrl", mo=True,
                                        skipTranslate=["x", "y", "z"])
                    list_fk_control.append(f"{namespace}:legUpperRGT_ctrl")

            # Left Leg
            if "jnt_l_legWrist" in str(loc):
                if self.ik_to_fk_leg_left_cb.isChecked():
                    cm.parentConstraint(loc, f"{namespace}:legAnkleLFT_ctrl", mo=True)
                    list_fk_control.append(f"{namespace}:legAnkleLFT_ctrl")
            if "jnt_l_leg_lowerTwist_000" in str(loc):
                if self.ik_to_fk_leg_left_cb.isChecked():
                    cm.parentConstraint(loc, f"{namespace}:legKneeLFT_ctrl", mo=True)
                    list_fk_control.append(f"{namespace}:legKneeLFT_ctrl")
            if "jnt_l_leg_upperTwist_000" in str(loc):
                if self.ik_to_fk_leg_left_cb.isChecked():
                    cm.parentConstraint(loc, f"{namespace}:legUpperLFT_ctrl", mo=True,
                                        skipTranslate=["x", "y", "z"])
                    list_fk_control.append(f"{namespace}:legUpperLFT_ctrl")

        cm.select(list_fk_control)

        eval(
            'bakeResults -simulation true -t "{0}:{1}" -sampleBy 1 -oversamplingRate 1 '
            '-disableImplicitControl true -preserveOutsideKeys true -sparseAnimCurveBake false '
            '-removeBakedAttributeFromLayer false -removeBakedAnimFromLayer false -bakeOnOverrideLayer '
            'false -minimizeRotation true -controlPoints false -shape false;'.format(
                min_time, max_time))

        cm.delete(list_loc_bake)


# noinspection PyMethodMayBeStatic,PyAttributeOutsideInit,PyMethodOverriding
class MainWindow(QtWidgets.QDialog):
    WINDOW_TITLE = "M2 Bake"

    SCRIPTS_DIR = cm.internalVar(userScriptDir=True)
    ICON_DIR = os.path.join(SCRIPTS_DIR, 'Thi/Icon')

    dlg_instance = None

    @classmethod
    def display(cls):
        if not cls.dlg_instance:
            cls.dlg_instance = MainWindow()

        if cls.dlg_instance.isHidden():
            cls.dlg_instance.show()

        else:
            cls.dlg_instance.raise_()
            cls.dlg_instance.activateWindow()

    @classmethod
    def maya_main_window(cls):
        """

        Returns: The Maya main window widget as a Python object

        """
        main_window_ptr = OMUI.MQtUtil.mainWindow()
        return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)

    def __init__(self):
        super(MainWindow, self).__init__(self.maya_main_window())

        self.setWindowTitle(self.WINDOW_TITLE)
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)

        self.geometry = None

        self.setMinimumSize(500, 200)
        self.setMaximumSize(500, 200)
        self.create_widget()
        self.create_layouts()
        self.create_connections()

    def create_widget(self):
        self.content_layout = QtWidgets.QHBoxLayout()
        self.content_layout.addWidget(M2Bake())

        self.close_btn = QtWidgets.QPushButton("Close")

    def create_layouts(self):

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addLayout(self.content_layout)

    def create_connections(self):
        self.close_btn.clicked.connect(self.close)

    def showEvent(self, e):
        super(MainWindow, self).showEvent(e)

        if self.geometry:
            self.restoreGeometry(self.geometry)

    def closeEvent(self, e):
        super(MainWindow, self).closeEvent(e)

        self.geometry = self.saveGeometry()
