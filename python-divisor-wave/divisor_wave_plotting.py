"""
Complex_Plotting.py
    The Complex Plotting class is a set of tools for plotting in the complex plane utilizing matplotlib.
    The Tool is capable of graphing polynomial functions, trig functions, infinite summations, and infinite
    products in the complex plane. These products are related to the distribution of prime numbers and the Riemann
    Hypothesis. The methods in call methods from the file Special_Functions.py for infinite product formulas.
4/9/2023
@LeoBorcherding
"""

import os
import pprint
import subprocess
import sys

import numpy as np
#import pyqtgraph as pg
import matplotlib.pyplot as plt

from matplotlib.colors import ListedColormap
from matplotlib import ticker
from matplotlib import cm

from Special_Functions import Special_Functions

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QPushButton, QVBoxLayout

# print(sys.path)
plt.style.use('dark_background')

# -----------------------------------------------------------------------------------------------------------------
class Complex_Plotting_GUI_MOD :
    # -----------------------------------------------------------------------------------------------------------------
    def __init__(self, plot_type):
        """
        Initialization the Special_Functions Object
        """
    class MyMplCanvas(FigureCanvas):
        def __init__(self, parent=None, width=5, height=4, dpi=100):
            fig = Figure(figsize=(width, height), dpi=dpi)
            self.axes = fig.add_subplot(111, projection='3d')
            super(MyMplCanvas, self).__init__(fig)

        # -----------------------------------------------------------------------------------------------------------------
        def create_plot_3D(self, color_map_3D, Normalize_type):

            # calculate special functions object f(z)
            lamda_function_array = special_functions_object.lamda_function_library(Normalize_type)

            R = self.resolution_3D
            X = np.arange(self.x_min_3D, self.x_max_3D, R)
            Y = np.arange(self.y_min_3D, self.y_max_3D, R)

            X, Y = np.meshgrid(X, Y)
            xn, yn = X.shape
            W = X * 0

            for xk in range(xn):
                for yk in range(yn):
                    try:
                        z = complex(X[xk, yk], Y[xk, yk])
                        w = float(lamda_function_array(z))

                        if w != w:
                            raise ValueError
                        W[xk, yk] = w

                    except (ValueError, TypeError, ZeroDivisionError):
                        # can handle special values here
                        pass

            # -----------------------------------------------------------------------------------------------------------------------
            # Set up the plot
            fig = plt.figure(figsize=(19, 11))

            # create 3d subplot
            ax = fig.add_subplot(111, projection='3d')

            # Set initial plot angles
            # ax.view_init(elev=30, azim=70)
            ax.view_init(elev=30, azim=-70)

            ax.dist = 10
            ax.set_box_aspect((5, 5, 1))
            ax.auto_scale_xyz([-1, 1], [-1, 1], [-1, 1])

            # Set the aspect ratio to be 1:1:0.5 # Was originally that ratio
            ax.set_box_aspect((5, 5, 1))

            if color_map_3D == "1":
                ax.plot_surface(X, Y, W, rstride=1, cstride=1, cmap=cm.prism)
            if color_map_3D == "2":
                ax.plot_surface(X, Y, W, rstride=1, cstride=1, cmap=cm.jet)
            if color_map_3D == "3":
                ax.plot_surface(X, Y, W, rstride=1, cstride=1, cmap=cm.plasma)
            if color_map_3D == "4":
                ax.plot_surface(X, Y, W, rstride=1, cstride=1, cmap=cm.viridis)
            if color_map_3D == "5":
                ax.plot_surface(X, Y, W, rstride=1, cstride=1, cmap=cm.magma)

            # Adjust grid line size
            # ax.tick_params(axis='both', which='major', pad=10, width=2)  # You can adjust pad and width as needed

            ax.set_xlabel('Real Axis')
            ax.set_ylabel('Imaginary Axis')
            ax.set_zlabel('Value')
            ax.set_title(f"Product of Sin(x) via Sin(x) product Representation")
            plt.draw()
            plt.show()

            return

    class MyWindow(QMainWindow):
        def __init__(self, plot_type, color_map, Normalize_type):
            super(MyWindow, self).__init__()
            self.canvas = Complex_Plotting_GUI_MOD.MyMplCanvas(self, width=5, height=4, dpi=100)

            # Create a button
            self.button = QPushButton('Update Plot')
            self.button.clicked.connect(self.update_plot)

            # Create a layout and add the button and canvas to it
            layout = QVBoxLayout()
            layout.addWidget(self.canvas)
            layout.addWidget(self.button)  # Add the button to the layout

            # Create a widget, set its layout, and set it as the central widget
            widget = QWidget()
            widget.setLayout(layout)
            self.setCentralWidget(widget)

            # Store the plot parameters
            self.plot_type = plot_type
            self.color_map = color_map
            self.Normalize_type = Normalize_type

        def update_plot(self):
            # Update the plot parameters here...
            if self.plot_type == "2D":
                self.canvas.create_plot_2D(self.color_map, self.Normalize_type)
            elif self.plot_type == "3D":
                self.canvas.create_plot_3D(self.color_map, self.Normalize_type)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Complex_Plotting_GUI_MOD.MyWindow(plot_type, color_map_2D if plot_type == "2D" else color_map_3D, Normalize_type)
    window.show()
    sys.exit(app.exec_())