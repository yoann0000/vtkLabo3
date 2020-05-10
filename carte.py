"""
!!!Important!!!
Quand on essaye de lacer le programe avec les 3001x3001 points on obtient cette erreure au moment du render
"Process finished with exit code -1073740791 (0xC0000409)"
Du coup pour remédier à cela nous avons render une plus petite image (2001x2001) pour quand meme avoir qqch a montrer.
les lignes impactées sont 41, 45, 79, 80

Beaucoup de code a été inspiré de "https://lorensen.github.io/VTKExamples/site/Python/" mais j'ai oublié de noter
les exemples specifiques
"""

import vtk
import math

# static values
latitude_start = 45
longitude_start = 5
advance = 2.5
earth_radius = 6371009
sea_level = 370


def polar2cart(r, theta, phi):
    thetaR = theta * (math.pi / 180)
    phiR = phi * (math.pi / 180)
    return [
        r * math.sin(thetaR) * math.cos(phiR),
        r * math.sin(thetaR) * math.sin(phiR),
        r * math.cos(thetaR)
    ]


def radius(point):
    return round(math.sqrt(point[0] ** 2 + point[1] ** 2 + point[2] ** 2))


def getAltitudes(path):
    file = open(path, "r")
    dimensions = file.readline().split()
    latitude = int(dimensions[0])
    longitude = int(dimensions[1])

    altitudesTable = []
    for i in range(0, 2000):  # for i in range(0, latitude):
        line = file.readline()
        altitudes = line.rstrip().split(" ")
        altitude_line = []
        for j in range(0, 2000):  # for i in range(0, longitude):
            altitude_line.append(int(altitudes[j]))
        altitudesTable.append(altitude_line)
    file.close()
    return [[latitude, longitude], altitudesTable]


def isWater(point, pointPosition, altitudesTable):
    if radius(point) - earth_radius <= sea_level:
        return True
    else:
        x = pointPosition[0]
        y = pointPosition[1]
        alts = [altitudesTable[x - 1][y - 1], altitudesTable[x][y - 1], altitudesTable[x + 1][y - 1],
                altitudesTable[x - 1][y], altitudesTable[x][y], altitudesTable[x + 1][y],
                altitudesTable[x - 1][y + 1], altitudesTable[x][y + 1], altitudesTable[x + 1][y + 1]]
        return len(set(alts)) == 1


def main():
    # get altitude table
    info = getAltitudes("altitudes.txt")
    print("altitudes gotten")
    altitudesTable = info[1]
    width = info[0][0]
    height = info[0][1]

    step_latitude = advance / width
    step_longitude = advance / height

    # comment these lines if not using the reduced altitude list
    width = 2000
    height = 2000

    # color lut
    colorLookupTable = vtk.vtkLookupTable()
    colorLookupTable.SetTableRange(0, 2000)
    colorLookupTable.SetHueRange(0.5, 0)
    colorLookupTable.SetSaturationRange(1.0, 0)
    colorLookupTable.SetValueRange(0.5, 1.0)
    colorLookupTable.Build()

    polyData = vtk.vtkPolyData()
    points = vtk.vtkPoints()
    cells = vtk.vtkCellArray()
    scalars = vtk.vtkFloatArray()

    # get points and associated scalars
    for x in range(0, width):
        for y in range(0, height):
            coords = polar2cart(earth_radius + altitudesTable[x][y],
                                latitude_start + (x * step_latitude),
                                longitude_start + (y * step_longitude))
            points.InsertNextPoint(coords[1], coords[2], coords[0])

            scalars.InsertTuple1(height * x + y, altitudesTable[x][y])
    print("points and scalars done")

    # reset scalars for bodies of water
    for x in range(0, width):
        for y in range(0, height):
            point = 3 * [0.0]
            points.GetPoint(height * x + y, point)
            if (0 < x < width - 1) and (0 < y < height - 1) and isWater(point, [x, y], altitudesTable):
                scalars.SetValue(height * x + y, 0)
    print("water bodies done")

    # topology using a cell array
    for x in range(0, width - 1):
        cells.InsertNextCell((height - 1) * 2)
        for y in range(0, height - 1):
            cells.InsertCellPoint(height * x + y)
            cells.InsertCellPoint(height * (x + 1) + y)
    print("cells done")

    # add points cells and scalars to the polydata
    polyData.SetPoints(points)
    polyData.SetStrips(cells)
    polyData.GetPointData().SetScalars(scalars)

    # rotate the polydata to render as a top-down view
    transform = vtk.vtkTransform()
    filtre = vtk.vtkTransformPolyDataFilter()
    filtre.SetInputData(polyData)
    filtre.SetTransform(transform)
    transform.RotateX(47.5)
    filtre.Update()

    # Create a mapper
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(filtre.GetOutputPort())
    mapper.SetLookupTable(colorLookupTable)
    mapper.UseLookupTableScalarRangeOn()

    # make an actor
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)

    # make the renderer and add a trackball interactor
    renderer = vtk.vtkRenderer()
    renderer.AddActor(actor)
    renderer.SetBackground(.1, .2, .3)

    renderWindow = vtk.vtkRenderWindow()
    renderWindow.SetSize(720, 1280)
    renderWindow.AddRenderer(renderer)

    renderWindowInteractor = vtk.vtkRenderWindowInteractor()
    renderWindowInteractor.SetRenderWindow(renderWindow)
    renderWindowInteractor.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())

    renderWindowInteractor.Initialize()
    renderWindowInteractor.Render()

    # screenshot code:
    w2if = vtk.vtkWindowToImageFilter()
    w2if.SetInput(renderWindow)
    w2if.Update()

    writer = vtk.vtkPNGWriter()
    writer.SetFileName("map.png")
    writer.SetInputConnection(w2if.GetOutputPort())
    writer.Write()

    renderWindowInteractor.Start()


if __name__ == '__main__':
    main()
