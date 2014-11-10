"""
CommandLine:
    # Regenerate command
    python ibeis/control/templates.py
    python ibeis/control/templates.py --dump-autogen-controller
"""
import utool as ut


#
#
#-----------------
# --- HEADER ---
#-----------------


Theader_ibeiscontrol = ut.codeblock(
    r'''
    # STARTBLOCK
    """
    Autogenerated IBEISController functions

    TemplateInfo:
        autogen_time = {timestamp}

    ToRegenerate:
        python ibeis/control/templates.py --dump-autogen-controller
    """
    from __future__ import absolute_import, division, print_function
    import functools  # NOQA
    import six  # NOQA
    from six.moves import map, range  # NOQA
    from ibeis import constants
    from ibeis.control.IBEISControl import IBEISController
    import utool  # NOQA
    import utool as ut  # NOQA
    print, print_, printDBG, rrr, profile = ut.inject(__name__, '[autogen_ibsfuncs]')

    # Create dectorator to inject these functions into the IBEISController
    register_ibs_aliased_method   = ut.make_class_method_decorator((IBEISController, 'autogen'))
    register_ibs_unaliased_method = ut.make_class_method_decorator((IBEISController, 'autogen'))


    def register_ibs_method(func):
        aliastup = (func, 'autogen_' + ut.get_funcname(func))
        register_ibs_unaliased_method(func)
        register_ibs_aliased_method(aliastup)
        return func
    # ENDBLOCK
    ''')


#
#
#-----------------
# --- ADDERS ---
#-----------------


Tadder_pl_dependant = ut.codeblock(
    r'''
    # STARTBLOCK
    #@adder
    def add_{parent}_{leaf}s({self}, {parent}_rowid_list, qreq_=None):
        """ {parent}.{leaf}.add({parent}_rowid_list)

        CRITICAL FUNCTION MUST EXIST FOR ALL DEPENDANTS
        Adds / ensures / computes a dependant property

        Args:
             {parent}_rowid_list

        Returns:
            returns config_rowid of the current configuration

        TemplateInfo:
            Tadder_pl_dependant
            parent = {parent}
            leaf = {leaf}

        Example:
            >>> # ENABLE_DOCTEST
            >>> import ibeis
            >>> {self} = ibeis.opendb('testdb1')
            >>> {parent}_rowid_list = {self}.get_valid_{parent}_rowids()
            >>> qreq_ = None
            >>> {leaf}_rowid_list = {self}.add_{parent}_{leaf}s({parent}_rowid_list, qreq_=qreq_)
        """
        #REM raise NotImplementedError('this code is a stub, you must populate it')
        from ibeis.model.preproc import preproc_{leaf}
        # Get requested configuration id
        config_rowid = {self}.get_{leaf}_config_rowid(qreq_=qreq_)
        # Find leaf rowids that need to be computed
        {leaf}_rowid_list = get_{parent}_{leaf}_rowids_({self}, {parent}_rowid_list, qreq_=qreq_)
        # Get corresponding "dirty" parent rowids
        dirty_{parent}_rowid_list = utool.get_dirty_items({parent}_rowid_list, {leaf}_rowid_list)
        if len(dirty_{parent}_rowid_list) > 0:
            if utool.VERBOSE:
                print('[{self}] adding %d / %d {leaf}' % (len(dirty_{parent}_rowid_list), len({parent}_rowid_list)))
            # Dependant columns do not need true from_superkey getters.
            # We can use the Tgetter_pl_dependant_rowids_ instead
            get_rowid_from_superkey = functools.partial({self}.get_{parent}_{leaf}_rowids_, qreq_=qreq_)
            {leaf_other_propname_lists} = preproc_{leaf}.add_{leaf}_params_gen({self}, {parent}_rowid_list)
            params_iter = (({parent}_rowid, config_rowid, {leaf_other_propnames})
                           for {parent}_rowid, {leaf_other_propnames} in
                           zip({parent}_rowid_list, {leaf_other_propname_lists}))
            colnames = {nonprimary_leaf_colnames}
            {leaf}_rowid_list = {self}.{dbself}.add_cleanly({LEAF_TABLE}, colnames, params_iter, get_rowid_from_superkey)
        return {leaf}_rowid_list
    # ENDBLOCK
    '''
)


Tadder_rl_dependant = ut.codeblock(
    r'''
    # STARTBLOCK
    #@adder
    def add_{root}_{leaf}s({self}, {root}_rowid_list, qreq_=None):
        """ {leaf}_rowid_list <- {root}.{leaf}.ensure({root}_rowid_list)

        Adds / ensures / computes a dependant property
        returns config_rowid of the current configuration

        CONVENIENCE FUNCTION

        Args:
            {root}_rowid_list

        TemplateInfo:
            Tadder_rl_dependant
            root = {root}
            leaf = {leaf}

        Example:
            >>> # ENABLE_DOCTEST
            >>> import ibeis
            >>> {self} = ibeis.opendb('testdb1')
            >>> {root}_rowid_list = {self}.get_valid_{root}_rowids()
            >>> qreq_ = None
            >>> {leaf}_rowid_list = {self}.add_{root}_{leaf}s({root}_rowid_list, qreq_=qreq_)
        """
        {leaf_parent}_rowid_list = {self}.get_{root}_{leaf_parent}_rowids({root}_rowid_list, qreq_=qreq_, ensure=True)
        {leaf}_rowid_list = add_{leaf_parent}_{leaf}s({self}, {leaf_parent}_rowid_list, qreq_=qreq_)
        return {leaf}_rowid_list
    # ENDBLOCK
    '''
)


#
#
#-----------------
# --- CONFIG ---
#-----------------

Tcfg_rowid_getter = ut.codeblock(
    r'''
    # STARTBLOCK
    #@ider
    def get_{leaf}_config_rowid({self}, qreq_=None):
        """ {leaf}_cfg_rowid = {leaf}.config_rowid()

        returns config_rowid of the current configuration
        Config rowids are always ensured

        Returns:
            {leaf}_cfg_rowid

        TemplateInfo:
            Tcfg_rowid_getter
            leaf = {leaf}

        Example:
            >>> # ENABLE_DOCTEST
            >>> import ibeis; {self} = ibeis.opendb('testdb1')
            >>> {leaf}_cfg_rowid = {self}.get_{leaf}_config_rowid()
        """
        if qreq_ is not None:
            {leaf}_cfg_suffix = qreq_.qparams.{leaf}_cfgstr
            # TODO store config_rowid in qparams
        else:
            {leaf}_cfg_suffix = {self}.cfg.{leaf}_cfg.get_cfgstr()
        {leaf}_cfg_rowid = {self}.add_config({leaf}_cfg_suffix)
        return {leaf}_cfg_rowid
    # ENDBLOCK
    '''
)


#
#
#-----------------
# --- DELETERS ---
#-----------------

# DELETER LINES
Tline_pc_dependant_delete = ut.codeblock(
    r'''
    # STARTBLOCK
    _{child}_rowid_list = get_{parent}_{child}_rowids_({self}, {parent}_rowid_list, qreq_=qreq_)
    {child}_rowid_list = ut.filter_Nones(_{child}_rowid_list)
    {self}.delete_{child}({child}_rowid_list)
    # ENDBLOCK
    '''
)


# DELETER RL_DEPEND
#{pc_dependant_delete_lines}
Tdeleter_rl_depenant = ut.codeblock(
    r'''
    # STARTBLOCK
    #@deleter
    #@cache_invalidator({ROOT_TABLE})
    def delete_{root}_{leaf}({self}, {root}_rowid_list, qreq_=None):
        """ {root}.{leaf}.delete({root}_rowid_list)

        Args:
            {root}_rowid_list

        TemplateInfo:
            Tdeleter_rl_depenant
            root = {root}
            leaf = {leaf}
        """
        if utool.VERBOSE:
            print('[{self}] deleting %d {root}s leaf nodes' % len({root}_rowid_list))
        # Delete any dependants
        _{leaf}_rowid_list = {self}.get_{root}_{leaf}_rowids({root}_rowid_list, qreq_=qreq_, ensure=False)
        {leaf}_rowid_list = ut.filter_Nones(_{leaf}_rowid_list)
        {self}.delete_{leaf}({leaf}_rowid_list)
    # ENDBLOCK
    '''
)


# DELETER NATIVE
Tdeleter_native_tbl = ut.codeblock(
    r'''
    # STARTBLOCK
    #@deleter
    #@cache_invalidator({TABLE})
    def delete_{tbl}({self}, {tbl}_rowid_list):
        """ {tbl}.delete({tbl}_rowid_list)

        delete {tbl} rows

        Args:
            {tbl}_rowid_list

        TemplateInfo:
            Tdeleter_native_tbl
            tbl = {tbl}

        Tdeleter_native_tbl
        """
        from ibeis.model.preproc import preproc_{leaf}
        if utool.VERBOSE:
            print('[{self}] deleting %d {tbl} rows' % len({tbl}_rowid_list))
        # Prepare: Delete externally stored data (if any)
        preproc_{leaf}.on_delete({self}, {tbl}_rowid_list)
        # Finalize: Delete self
        {self}.{dbself}.delete_rowids({TABLE}, {tbl}_rowid_list)
    # ENDBLOCK
    '''
)

#
#
#-----------------
# --- IDERS ---
#-----------------


Tider_all_rowids = ut.codeblock(
    r'''
    # STARTBLOCK
    #@ider
    def _get_all_{tbl}_rowids({self}):
        """ all_{tbl}_rowids <- {tbl}.get_all_rowids()

        Returns:
            list_ (list): unfiltered {tbl}_rowids

        TemplateInfo:
            Tider_all_rowids
            tbl = {tbl}
        """
        all_{tbl}_rowids = {self}.{dbself}.get_all_rowids({TABLE})
        return all_{tbl}_rowids
    # ENDBLOCK
    '''
)

#
#
#-----------------
# --- GETTERS ---
#-----------------

# LINES GETTER
Tline_pc_dependant_rowid = ut.codeblock(
    r'''
    # STARTBLOCK
    {child}_rowid_list = {self}.get_{parent}_{child}_rowids({parent}_rowid_list, qreq_=qreq_, ensure=ensure)
    # ENDBLOCK
    '''
)

# RL GETTER COLUMN
Tgetter_rl_pclines_dependant_column = ut.codeblock(
    r'''
    # STARTBLOCK
    #@getter
    def get_{root}_{col}s({self}, {root}_rowid_list, qreq_=None, ensure=False):
        """ {leaf}_rowid_list <- {root}.{leaf}.rowids[{root}_rowid_list]

        Get {col} data of the {root} table using the dependant {leaf} table

        Args:
            {root}_rowid_list (list):

        Returns:
            list: {col}_list

        TemplateInfo:
            Tgetter_rl_pclines_dependant_column
            root = {root}
            col  = {col}
            leaf = {leaf}
        """
        # Get leaf rowids
        {pc_dependant_rowid_lines}
        # Get col values
        {col}_list = {self}.get_{leaf}_{col}({leaf}_rowid_list)
        return {col}_list
    # ENDBLOCK
    ''')

# RL GETTER ROWID
Tgetter_rl_dependant_rowids = ut.codeblock(
    r'''
    # STARTBLOCK
    #@getter
    def get_{root}_{leaf}_rowids({self}, {root}_rowid_list, qreq_=None, ensure=False, eager=True, nInput=None):
        """ {leaf}_rowid_list = {root}.{leaf}.rowids[{root}_rowid_list]

        Get {leaf} rowids of {root} under the current state configuration.

        Args:
            {root}_rowid_list (list):

        Returns:
            list: {leaf}_rowid_list

        TemplateInfo:
            Tgetter_rl_dependant_rowids
            root        = {root}
            leaf_parent = {leaf_parent}
            leaf        = {leaf}

        Example:
            >>> # ENABLE_DOCTEST
            >>> import ibeis
            >>> {self} = ibeis.opendb('testdb1')
            >>> {root}_rowid_list = {self}.get_valid_{root}_rowids()
            >>> qreq_ = None
            >>> ensure = False
            >>> {leaf}_rowid_list1 = {self}.get_{root}_{leaf}_rowids({root}_rowid_list, qreq_, ensure)
            >>> print({leaf}_rowid_list1)
            >>> ensure = True
            >>> {leaf}_rowid_list2 = {self}.get_{root}_{leaf}_rowids({root}_rowid_list, qreq_, ensure)
            >>> print({leaf}_rowid_list2)
            >>> ensure = False
            >>> {leaf}_rowid_list3 = {self}.get_{root}_{leaf}_rowids({root}_rowid_list, qreq_, ensure)
            >>> print({leaf}_rowid_list3)
        """
        if ensure:
            # Ensuring dependant columns is equivalent to adding cleanly
            return {self}.add_{root}_{leaf}s({root}_rowid_list, qreq_=qreq_)
        else:
            # Get leaf_parent rowids
            {leaf_parent}_rowid_list = {self}.get_{root}_{leaf_parent}_rowids({root}_rowid_list, qreq_=qreq_, ensure=False)
            colnames = ({LEAF}_ROWID,)
            config_rowid = {self}.get_{leaf}_config_rowid(qreq_=qreq_)
            andwhere_colnames = ({LEAF_PARENT}_ROWID, CONFIG_ROWID,)
            params_iter = [({leaf_parent}_rowid, config_rowid,) for {leaf_parent}_rowid in {leaf_parent}_rowid_list]
            {leaf}_rowid_list = {self}.{dbself}.get_where2(
                {LEAF_TABLE}, colnames, params_iter, andwhere_colnames, eager=eager, nInput=nInput)
            return {leaf}_rowid_list
    # ENDBLOCK
    ''')


# PL GETTER ROWID
Tgetter_pl_dependant_rowids_ = ut.codeblock(
    r'''
    # STARTBLOCK
    #@getter
    def get_{parent}_{leaf}_rowids_({self}, {parent}_rowid_list, qreq_=None, eager=True, nInput=None):
        """
        equivalent to get_{parent}_{leaf}_rowids_ except ensure cannot be specified

        You basically save a stack frame by calling this, because
        get_{parent}_{leaf}_rowids just calls this function if ensure is False
        """
        colnames = ({LEAF}_ROWID,)
        config_rowid = {self}.get_{leaf}_config_rowid(qreq_=qreq_)
        andwhere_colnames = ({PARENT}_ROWID, CONFIG_ROWID,)
        params_iter = (({parent}_rowid, config_rowid,) for {parent}_rowid in {parent}_rowid_list)
        {leaf}_rowid_list = {self}.{dbself}.get_where2(
            {LEAF_TABLE}, colnames, params_iter, andwhere_colnames, eager=eager, nInput=nInput)
        return {leaf}_rowid_list
    # ENDBLOCK
    ''')


# PL GETTER ROWID
Tgetter_pl_dependant_rowids = ut.codeblock(
    r'''
    # STARTBLOCK
    #@getter
    def get_{parent}_{leaf}_rowids({self}, {parent}_rowid_list, qreq_=None, ensure=False, eager=True, nInput=None):
        """ {leaf}_rowid_list <- {parent}.{leaf}.rowids[{parent}_rowid_list]

        get {leaf} rowids of {parent} under the current state configuration
        if ensure is True, this function is equivalent to add_{parent}_{leaf}s

        Args:
            {parent}_rowid_list (list):
            ensure (bool): default false

        Returns:
            list: {leaf}_rowid_list

        TemplateInfo:
            Tgetter_pl_dependant_rowids
            parent = {parent}
            leaf = {leaf}

        Timeit:
            >>> from {autogen_modname} import *  # NOQA
            >>> import ibeis
            >>> {self} = ibeis.opendb('testdb1')
            >>> # Test to see if there is any overhead to injected vs native functions
            >>> %timeit get_{parent}_{leaf}_rowids({self}, {parent}_rowid_list)
            >>> %timeit {self}.get_{parent}_{leaf}_rowids({parent}_rowid_list)

        Example:
            >>> # ENABLE_DOCTEST
            >>> from {autogen_modname} import *  # NOQA
            >>> import ibeis
            >>> {self} = ibeis.opendb('testdb1')
            >>> {parent}_rowid_list = {self}.get_valid_{parent}_rowids()
            >>> qreq_ = None
            >>> ensure = False
            >>> {leaf}_rowid_list = {self}.get_{parent}_{leaf}_rowids({parent}_rowid_list, qreq_, ensure)
            >>> assert len({leaf}_rowid_list) == len({parent}_rowid_list)
        """
        if ensure:
            {leaf}_rowid_list = add_{parent}_{leaf}s({self}, {parent}_rowid_list, qreq_=qreq_)
        else:
            {leaf}_rowid_list = get_{parent}_{leaf}_rowids_({self}, {parent}_rowid_list, qreq_=qreq_)
        return {leaf}_rowid_list
    # ENDBLOCK
    ''')


# PL GETTER ALL ROWID
Tgetter_rl_dependant_all_rowids = ut.codeblock(
    r'''
    # STARTBLOCK
    #@getter
    def get_{root}_{leaf}_all_rowids({self}, {root}_rowid_list, eager=True, nInput=None):
        """ {leaf}_rowid_list <- {root}.{leaf}.all_rowids([{root}_rowid_list])

        Gets {leaf} rowids of {root} under the current state configuration.

        Args:
            {root}_rowid_list (list):

        Returns:
            list: {leaf}_rowid_list

        TemplateInfo:
            Tgetter_rl_dependant_all_rowids
            root = {root}
            leaf = {leaf}
        """
        # FIXME: broken
        colnames = ({LEAF_PARENT}_ROWID,)
        {leaf}_rowid_list = {self}.{dbself}.get(
            {LEAF_TABLE}, colnames, {root}_rowid_list,
            id_colname={ROOT}_ROWID, eager=eager, nInput=nInput)
        return {leaf}_rowid_list
    # ENDBLOCK
    ''')


# NATIVE ROWID GET FROM SUPERKEY
#id_iter = (({tbl}_rowid,) for {tbl}_rowid in {tbl}_rowid_list)
Tgetter_native_rowid_from_superkey = ut.codeblock(
    r'''
    # STARTBLOCK
    #@getter
    def get_{tbl}_rowid_from_superkey({self}, {superkey_args}, eager=True, nInput=None):
        """ {tbl}_rowid_list <- {tbl}[{superkey_args}]

        Args:
            superkey lists: {superkey_args}

        Returns:
            {tbl}_rowid_list

        TemplateInfo:
            Tgetter_native_rowid_from_superkey
            tbl = {tbl}
        """
        colnames = ({TBL}_ROWID),
        # FIXME: col_rowid is not correct
        params_iter = zip({superkey_args})
        andwhere_colnames = [{superkey_args}]
        {tbl}_rowid_list = {self}.{dbself}.get_where2(
            {TABLE}, colnames, params_iter, andwhere_colnames, eager=eager, nInput=nInput)
        return {tbl}_rowid_list
    # ENDBLOCK
    ''')

# NATIVE COLUMN GETTER
Tgetter_table_column = ut.codeblock(
    r'''
    # STARTBLOCK
    #@getter
    def get_{tbl}_{col}({self}, {tbl}_rowid_list, eager=True):
        """ {col}_list <- {tbl}.{col}[{tbl}_rowid_list]

        gets data from the "native" column "{col}" in the "{tbl}" table

        Args:
            {tbl}_rowid_list (list):

        Returns:
            list: {col}_list

        TemplateInfo:
            Tgetter_table_column
            col = {col}
            tbl = {tbl}
        """
        id_iter = {tbl}_rowid_list
        colnames = ({COLNAME},)
        {col}_list = {self}.{dbself}.get({TABLE}, colnames, id_iter, id_colname='rowid', eager=eager)
        return {col}_list
    # ENDBLOCK
    ''')

#
#
#-----------------
# --- SETTERS ---
#-----------------


# NATIVE COL SETTER
Tsetter_native_column = ut.codeblock(
    r'''
    # STARTBLOCK
    #@setter
    def set_{tbl}_{col}({self}, {tbl}_rowid_list, {col}_list):
        """ {col}_list -> {tbl}.{col}[{tbl}_rowid_list]

        Args:
            {tbl}_rowid_list
            {col}_list

        TemplateInfo:
            Tsetter_native_column
            tbl = {tbl}
            col = {col}
        """
        id_iter = {tbl}_rowid_list
        colnames = ({COLNAME},)
        {self}.{dbself}.set({TABLE}, colnames, {col}_list, id_iter)
    # ENDBLOCK
    ''')


#
#
#-------------------------------
# --- UNFINISHED AND DEFERRED ---
#-------------------------------


# eg. get_chip_sizes
Tgetter_native_multicolumn = ut.codeblock(
    r'''
    # STARTBLOCK
    #@getter
    def get_{tbl}_{multicol}({self}, {tbl}_rowid_list):
        """
        Returns zipped tuple of information from {multicol} columns

        Tgetter_native_multicolumn

        Args:
            {tbl}_rowid_list (list):

        Returns:
            list: {multicol}_list
        """
        {multicol}_list  = {self}.{dbself}.get({TABLE}, ({MULTI_COLNAMES},), {tbl}_rowid_list)
        return {multicol}_list
    # ENDBLOCK
    ''')

Tsetter_native_multicolumn = ut.codeblock(
    r'''
    # STARTBLOCK
    def set_{tbl}_{multicol}({self}, {tbl}_rowid_list, vals_list):
        """
        Tsetter_native_multicolumn
        """
        {self}.{dbself}.set({TABLE}, ({MULTI_COLNAMES},), {tbl}_rowid_list)
        pass
    # ENDBLOCK
    ''')


Tdeleter_table_relation = ut.codeblock(
    r'''
    # STARTBLOCK
    #@deleter
    def delete_{tbl}_relations({self}, {tbl}_rowid_list):
        """
        Deletes the relationship between an {tbl} row and a label
        """
        {relation}_rowids_list = {self}.get_{tbl}_{relation}_rowids({tbl}_rowid_list)
        {relation}_rowid_list = utool.flatten({relation}_rowids_list)
        {self}.{dbself}.delete_rowids({RELATION_TABLE}, {relation}_rowid_list)
    # ENDBLOCK
    '''
)

Tadder_relationship = ut.codeblock(
    r'''
    # STARTBLOCK
    #@adder
    def add_{tbl1}_{tbl2}_relationship({self}, {tbl1}_rowid_list, {tbl2}_rowid_list):
        """
        Adds a relationship between an image and encounter

        Returns:
            {tbl1}_{tbl2}_relation_rowid_list

        TemplateInfo:
            Tadder_relationship
        """
        colnames = ('{tbl1}_rowid', '{tbl2}_rowid',)
        params_iter = list(zip({tbl1}_rowid_list, {tbl2}_rowid_list))
        get_rowid_from_superkey = {self}.get_{tbl1}_{tbl2}_relation_rowid_from_superkey
        superkey_paramx = (0, 1)
        {tbl1}_{tbl2}_relation_rowid_list = {self}.{dbself}.add_cleanly(
            {TABLE1}_{TABLE2}_RELATION_TABLE, colnames, params_iter, get_rowid_from_superkey, superkey_paramx)
        return {tbl1}_{tbl2}_relation_rowid_list
    # ENDBLOCK
    ''')


#
#
#-----------------
# --- FOOTER ---
#-----------------


Tfooter_ibeiscontrol = ut.codeblock(
    r'''
    # STARTBLOCK
    if __name__ == '__main__':
        """
        {main_docstr_body}
        """
        import multiprocessing
        multiprocessing.freeze_support()
        import utool as ut
        ut.doctest_funcs()
    # ENDBLOCK
    ''')
