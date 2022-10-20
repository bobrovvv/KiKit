from pcbnewTransition import pcbnew, isV6
import csv
import os
from pathlib import Path
import shutil
from kikit.fab.common import *
from kikit.common import *
from kikit.export import gerberImpl, dxfImpl, rezonitGerberPlotPlan, exportSettingsRezonit, assemblyDrawingExport, reviewFilesExport, renderBoardsExport

def collectBom(components, ignore):
    bom = {}
    for c in components:

        if getUnit(c) != 1:
            continue

        reference = getReference(c)

        if reference.startswith("#PWR") or reference.startswith("#FL") or reference.startswith("TP"):
            continue

        if reference in ignore:
            continue

        if hasattr(c, "in_bom") and not c.in_bom:
            continue

        footprint = None
        footprint = getField(c, "Footprint")
        value = None
        value = getField(c, "Value")
        manufacturer = None
        manufacturer = getField(c, "Mfr.")
        partNumber = None
        partNumber = getField(c, "Prt. number")
        description = None
        description = getField(c, "Value modifier")
        dnf = None
        dnf = getField(c, "fit_field")
        price = None    
        price = getField(c, "Price")
        cType = (
            value,
            manufacturer,
            partNumber,
            description,
            footprint,
            dnf,
            price
        )
        bom[cType] = bom.get(cType, []) + [reference]
    return bom

def bomToCsv(bomData, filename):
    with open(filename, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Item#", "Reference", "Qty", "Value", "Manufacturer", "Part Number", "Description", "Footprint", "DNF", "Price"])
        item_no = 1
        for cType, references in bomData.items():
            value, manufacturer, partNumber, description, footprint, dnf, price= cType
            writer.writerow([item_no, ",".join(references),
                            len(references),
                            value,
                            manufacturer,
                            partNumber,
                            description,
                            footprint,
                            dnf,
                            price
                            ])
            item_no += 1

def noFilter(footprint):
    return True

def exportRezonit(board, outputdir, assembly, schematic, ignore, nametemplate, drc):
    """
    Prepare fabrication files for Rezonit including their assembly service
    """
    ensureValidBoard(board)
    loadedBoard = pcbnew.LoadBoard(board)

    if drc:
        ensurePassingDrc(loadedBoard)

    refsToIgnore = parseReferences(ignore)
    removeComponents(loadedBoard, refsToIgnore)

    Path(outputdir).mkdir(parents=True, exist_ok=True)

    gerberdir = os.path.join(outputdir, "gerber")
    shutil.rmtree(gerberdir, ignore_errors=True)
    gerberImpl(board, gerberdir, settings=exportSettingsRezonit, plot_plan=rezonitGerberPlotPlan)
    archiveName = nametemplate.format("gerbers")
    shutil.make_archive(os.path.join(outputdir, archiveName), "zip", outputdir, "gerber")

    dxfdir = os.path.join(outputdir, "dxf")
    shutil.rmtree(dxfdir, ignore_errors=True)
    dxfImpl(board, dxfdir)
    archiveName = nametemplate.format("dxf")
    shutil.make_archive(os.path.join(outputdir, archiveName), "zip", outputdir, "dxf")

    if not assembly:
        return
    if schematic is None:
        raise RuntimeError("When outputing assembly data, schematic is required")

    ensureValidSch(schematic)
    components = extractComponents(schematic)
    bom = collectBom(components, refsToIgnore)
    posData = collectPosData(loadedBoard, correctionFields = "", bom=components, posFilter=noFilter)
    boardReferences = set([x[0] for x in posData])
    bom = {key: [v for v in val if v in boardReferences] for key, val in bom.items()}
    bom = {key: val for key, val in bom.items() if len(val) > 0}

    assemblydir = os.path.join(outputdir, "assembly")
    shutil.rmtree(assemblydir, ignore_errors=True)
    Path(assemblydir).mkdir(parents=True, exist_ok=True)

    posDataToFile(posData, os.path.join(assemblydir, nametemplate.format("pos") + ".csv"))
    bomToCsv(bom, os.path.join(assemblydir, nametemplate.format("bom") + ".csv"))
    assemblyDrawingExport(board, assemblydir)

    archiveName = nametemplate.format("assembly")
    shutil.make_archive(os.path.join(outputdir, archiveName), "zip", outputdir, "assembly")

    reviewfilesdir = os.path.join(outputdir, "review")
    shutil.rmtree(reviewfilesdir, ignore_errors=True)
    Path(reviewfilesdir).mkdir(parents=True, exist_ok=True)
    reviewFilesExport(board, reviewfilesdir)
    archiveName = nametemplate.format("review")
    shutil.make_archive(os.path.join(outputdir, archiveName), "zip", outputdir, "review")

    renderfilesdir = os.path.join(outputdir, "render")
    shutil.rmtree(renderfilesdir, ignore_errors=True)
    renderBoardsExport(board, outputdir)
    archiveName = nametemplate.format("render")
    shutil.make_archive(os.path.join(outputdir, archiveName), "zip", outputdir, "render")

    shutil.rmtree(assemblydir, ignore_errors=True)
    shutil.rmtree(gerberdir, ignore_errors=True)
    shutil.rmtree(dxfdir, ignore_errors=True)
    shutil.rmtree(reviewfilesdir, ignore_errors=True)
    shutil.rmtree(renderfilesdir, ignore_errors=True)


        # TBD
        # -------------------------
        # tmp = tempfile.mkdtemp()
        # export.gerberImpl(boardDesc["source"], tmp)
        # gerbers = [os.path.join(tmp, x) for x in os.listdir(tmp)]
        # subprocess.check_call(["zip", "-j", os.path.join(outputDirectory, boardDesc["gerbers"])] + gerbers)
        # shutil.rmtree(tmp)
        # shutil.copy(boardDesc["source"], os.path.join(outputDirectory, boardDesc["file"]))