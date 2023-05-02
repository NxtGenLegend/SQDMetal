from qiskit_metal.renderers.renderer_mpl.mpl_renderer import QMplRenderer
from qiskit_metal.qlibrary.core import QComponent
import numpy as np
from qiskit_metal.toolbox_python.attr_dict import Dict

def get_path(leDesign, component_name, trace_name='', pts_per_turn=25):
    df = leDesign.qgeometry.tables['path']
    df = df[df['component'] == leDesign.components[component_name].id]#['geometry'][0]
    if trace_name != '':
        df = df[df['name']==trace_name]
    else:
        df = df[df['subtract']==False]
    
    qmpl = QMplRenderer(None, leDesign, None)
    qmpl.options['resolution'] = str(pts_per_turn)
    df = qmpl.render_fillet(df)
    return df['geometry'].iloc[0], df

def get_path_point(frac_line, is_right_hand, leDesign, component_name, trace_name='', pts_per_turn=25):
    path, pathObj = get_path(leDesign, component_name, trace_name, pts_per_turn)
    lePath = np.array(path.coords[:])
    dists = np.linalg.norm(lePath[1:,:]-lePath[:-1,:], axis=1)
    total_dist = np.sum(dists)
    sum_dists = 0
    for m in range(dists.shape[0]):
        pt_frac = (frac_line*total_dist - sum_dists)/dists[m]
        if pt_frac <= 1.0:
            ptLine = np.array([ pt_frac*(lePath[m+1][0]-lePath[m][0])+lePath[m][0], pt_frac*(lePath[m+1][1]-lePath[m][1])+lePath[m][1] ])
            if is_right_hand:
                norm_vec = np.array([-lePath[m+1][1]-lePath[m][1], lePath[m+1][0]-lePath[m][0]])
                norm_vec /= np.linalg.norm(norm_vec)
                if not is_right_hand:
                    norm_vec = -norm_vec
            break
        sum_dists += dists[m]
    return ptLine, norm_vec, pathObj

class RouteJoint(QComponent):
    default_options = Dict(pathObj='', pathObjTraceName='', frac_line=0.5, is_right_hand=True)
    
    def make(self):
        p = self.p

        if self.options.pathObj == '':
            ptLine = np.array([0,0])
            norm_vec = np.array([1,0])
            width = 1e-6
        else:
            ptLine, norm_vec, pathObj = get_path_point(p.frac_line, p.is_right_hand, self._design, self.options.pathObj, self.options.pathObjTraceName)
            width = pathObj['width'].iloc[0]
        
        self.options.pos_x, self.options.pos_y = ptLine

        self.add_pin('a', [(ptLine+norm_vec).tolist(), ptLine.tolist()], width=width, input_as_norm=True)

