from Npp import *

editor.beginUndoAction()

lines = editor.getText().splitlines()
new_lines = []

counter = 0
for line in lines:
    if 'Completed-newstime-0.html' in line:
        new_line = line.replace('Completed-newstime-0.html', f'Completed-newstime-{counter}.html')
        counter += 1
    else:
        new_line = line
    new_lines.append(new_line)

editor.setText('\n'.join(new_lines))

editor.endUndoAction()
