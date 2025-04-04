from curvatureGlyph_merz import CurvaturePen
import vanilla as vui
from AppKit import NSRoundRectBezelStyle
from fontParts.world import RGlyph
from fontTools.pens.transformPen import TransformPointPen, TransformPen
from fontTools.misc.transform import Transform
from displaySubscriber import DisplaySuscriber
from mojo import subscriber, events
from mojo.pens import DecomposePointPen
from mojo.subscriber import registerGlyphEditorSubscriber
from merz import MerzPen
from curvatureVisualizatorSettings import (
    internalGetDefault,
    internalSetDefault,
    extensionKeyStub,
    extensionID
)



__DEBUG__ = True
# ====================================
# S U B S C R I B E R
# ====================================

class CurvatureVisualizatorSubscriber(DisplaySuscriber):
    debug = __DEBUG__

    title = "Curvature Visualizator"
    scale = None
    bgBaseLayer = None
    outlineType = None
    zoomVisualization = None
    absoluteVisualizationSize = None
    visualizationSize = None
    showOptionsButtonInGlyphWindow = None
    clockwise, counterclockwise = None, None
    def build(self):
        self.loadDefaults()


        window = self.getGlyphEditor()
        self.middlegroundContainer = window.extensionContainer(
            identifier=extensionKeyStub + "middleground",
            location="middleground",
            clear=True,
        )
        self.bgBaseLayer = self.middlegroundContainer.appendBaseSublayer()

        # controls
        self.optionsGroup = vui.Group((0, -200, -0, -0))
        self.optionsGroup.button = vui.Button((-141-6, -35-8, 120, 22),
                                        "Curvature Options",
                                        callback=self.curvatureOptionsCallback)
        nsObj = self.optionsGroup.button.getNSButton()
        nsObj.setBezelStyle_( NSRoundRectBezelStyle )
        window.addGlyphEditorSubview(self.optionsGroup)
        self.optionsGroup.show(False)
        self.showCurvatureOptions()
        events.addObserver(
            self, "extensionDefaultsChanged", extensionKeyStub + "defaultsChanged"
        )

    def loadDefaults(self):
        self.steps = internalGetDefault("exst_divisionSteps_EditText_int")
        self.colorPalette = (internalGetDefault("exst_fillColor_ColorWell"), internalGetDefault("exst_strokeColor_ColorWell"))
        self.strokeWidth = internalGetDefault("exst_strokeWidth_EditText_int")
        self.showOptionsButtonInGlyphWindow = internalGetDefault("exst_showOptionsButtonInGlyphWindow_CheckBox")
        self.showMe = internalGetDefault("isVisible")
        self.zoomVisualization = internalGetDefault("exst_zoomVisualization_CheckBox")
        self.absoluteVisualizationSize = internalGetDefault("exst_visualizationSize_Slider")["value"]
        visualizationType = internalGetDefault("exst_visualizationType_SegmentedButton_counterclockwise_clockwise_both")
        if visualizationType == 2:
            self.clockwise, self.counterclockwise = True, True
        elif visualizationType == 1:
            self.clockwise, self.counterclockwise = True, False
        elif visualizationType == 0:
            self.clockwise, self.counterclockwise = False, True

    def destroy(self):
        self.middlegroundContainer.clearSublayers()
        events.removeObserver(self, extensionKeyStub + "defaultsChanged")

    def toggleOn(self):
        if self.bgBaseLayer is None:
            return
        self.bgBaseLayer.setVisible(True)
        if self.pen is not None:
            # print("AAA")
            self.pen.resetMerzPens()
            self.pen.setLengthMultiplier(self.visualizationSize) # faster than self.drawPath(info)
            self.drawPath(dict(glyph=self.getGlyphEditor().getGlyph().asFontParts()))

    def toggleOff(self):
        if self.bgBaseLayer is None:
            return
        self.bgBaseLayer.setVisible(False)

    # # # # # # # # # # #
    # Option Button
    #
    @property
    def visualizationSize(self):
        value = self.absoluteVisualizationSize
        if self.zoomVisualization:
            value *= 1/self.scale
        return value

    def glyphEditorDidScale(self, info):
        self.scale = info["scale"]
        if self.zoomVisualization and self.pen is not None and self.showMe:
            self.pen.resetMerzPens()
            self.pen.setLengthMultiplier(self.visualizationSize) # faster than self.drawPath(info)
            self.drawPath(info)

    def curvatureOptionsCallback(self, sender):
        try:
            self.pop = vui.Popover((300, 170), preferredEdge='bottom', behavior='transient')

            y = 10
            self.pop.visualizationSizeText = vui.TextBox((10, y, -10, 20), 'Visualization Size')

            y += 22+10
            sliderDefaults =internalGetDefault("exst_visualizationSize_Slider")
            self.pop.visualizationSize_Slider_int = vui.Slider(
                (10, y, -10, 20),
                minValue=sliderDefaults.get("minValue"),
                maxValue=sliderDefaults.get("maxValue"),
                value=sliderDefaults.get("value"),
                callback=self.settingsCallback, continuous=True
            )

            y += 22+10
            self.pop.type = vui.TextBox((10, y, -10, 20), 'Visualization Type')

            y += 22+10
            self.pop.visualizationType_SegmentedButton_counterclockwise_clockwise_both = vui.SegmentedButton((10, y, -10, 20),
                         [dict(title="counterclockwise"), dict(title="clockwise"), dict(title="both")],
                        callback=self.settingsCallback)
            self.pop.visualizationType_SegmentedButton_counterclockwise_clockwise_both.set(
                internalGetDefault("exst_visualizationType_SegmentedButton_counterclockwise_clockwise_both")
            )

            y += 22+10
            self.pop.zoomVisualization_CheckBox = vui.CheckBox((10, y, 240, 20),
                        "zoom visualization",value=internalGetDefault("exst_zoomVisualization_CheckBox"),
                        callback=self.settingsCallback)

            self.pop.visualizationSize_Slider_int._id = "exst_visualizationSize_Slider"
            self.pop.visualizationType_SegmentedButton_counterclockwise_clockwise_both._id = "exst_visualizationType_SegmentedButton_counterclockwise_clockwise_both"
            self.pop.zoomVisualization_CheckBox._id = "exst_zoomVisualization_CheckBox"
            self.pop.open(parentView=sender.getNSButton(), preferredEdge='top')
        except:
            import traceback
            print(traceback.format_exc())

    def settingsCallback(self, sender):
        if "_Slider" in sender._id:
            value = sender.get()
            if "_SliderInt" in sender._id:
                value = int(value)

            sliderDefaults =internalGetDefault("exst_visualizationSize_Slider")
            value = dict(minValue=sliderDefaults.get("minValue"), maxValue=sliderDefaults.get("maxValue"), value=value)
            internalSetDefault(sender._id, value)

        elif "_CheckBox" in sender._id:
            internalSetDefault(sender._id, bool(sender.get()))

        else:
            internalSetDefault(sender._id, sender.get())

        events.postEvent(extensionID + ".defaultsChanged")

    def showCurvatureOptions(self):
        if self.showOptionsButtonInGlyphWindow:
            self.optionsGroup.show(self.showMe)
        else:
            self.optionsGroup.show(False)

    def extensionDefaultsChanged(self, event):
        self.loadDefaults()
        self.showCurvatureOptions()
        self.pen = CurvaturePen(steps=self.steps, lengthMultiplier=self.visualizationSize, clockwise=self.clockwise, counterclockwise=self.counterclockwise, colorPalette=self.colorPalette, strokeWidth=self.strokeWidth, parentLayer=self.bgBaseLayer)
        self.drawPath(dict(glyph=self.getGlyphEditor().getGlyph().asFontParts()))

    # def glyphEditorWantsContextualMenuItems(self, info):
    #     myMenuItems = [
    #         ("Curvature Type", self.contextualItemCallback)
    #     ]
    #     info["itemDescriptions"].extend(myMenuItems)

    # # # # # # # # # # #
    # Drawing
    #
    def setGlyph(self, info):
        self.scale = info["glyphEditor"].getGlyphViewScale()
        glyph = info["glyph"]
        self.pen = CurvaturePen(steps=self.steps, lengthMultiplier=self.visualizationSize, clockwise=self.clockwise, counterclockwise=self.counterclockwise, colorPalette=self.colorPalette, strokeWidth=self.strokeWidth, parentLayer=self.bgBaseLayer)

    def glyphEditorDidSetGlyph(self, info):
        self.setGlyph(info)
        self.drawPath(info)

    def glyphEditorDidUndo(self, info):
        try:
            self.pen.resetMerzPens()
            self.drawPath(info)
        except:
            import traceback
            print(traceback.format_exc())

    glyphEditorGlyphDidChangeOutlineDelay = 0
    def glyphEditorGlyphDidChangeOutline(self, info):
        try:
            self.pen.resetMerzPens()
            self.drawPath(info)
        except:
            import traceback
            print(traceback.format_exc())

    glyphEditorGlyphDidChangeContoursDelay = 0
    def glyphEditorGlyphDidChangeContours(self, info):
        try:
            self.pen.resetMerzPens()
            self.drawPath(info)
        except:
            import traceback
            print(traceback.format_exc())

    glyphEditorGlyphDidChangeMetricsDelay = 0
    def glyphEditorGlyphDidChangeMetrics(self, info):
        try:
            self.pen.resetMerzPens()
            self.drawPath(info)
        except:
            import traceback
            print(traceback.format_exc())

    def glyphEditorDidOpen(self, info):
        super().glyphEditorDidOpen(info)
        self.setGlyph(info)
        self.drawPath(info)
        self.showCurvatureOptions()


    pen = None
    def drawPath(self, info):
        if self.showMe:
            # Set up a decomposed glyph object
            glyph = info["glyph"]
            font = glyph.font
            self.decomp_glyph = RGlyph()
            self.decomp_glyph.width = glyph.width
            decomp_pen = DecomposePointPen(font, self.decomp_glyph.getPointPen())
            glyph.drawPoints(decomp_pen)
            self.decomp_glyph.draw(self.pen)
            self.pen.draw()

    def menuButtonWasPressed(self, nsMenuItem):
        if self.getButtonState():
            self.showMe = True
        else:
            self.showMe = False

        self.showCurvatureOptions()



registerGlyphEditorSubscriber(CurvatureVisualizatorSubscriber)