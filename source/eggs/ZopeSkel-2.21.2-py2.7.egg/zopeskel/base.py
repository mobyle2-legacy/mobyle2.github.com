import os
from textwrap import TextWrapper
import ConfigParser
from ConfigParser import SafeConfigParser
from paste.script import command
from paste.script import pluginlib
from paste.script import templates
from paste.script.templates import var as base_var
from paste.script.command import BadCommand
from paste.script.templates import BasicPackage
from zopeskel.vars import var, BooleanVar, StringChoiceVar
from zopeskel.vars import EASY, EXPERT, ALL
from zopeskel.vars import ValidationException


LICENSE_CATEGORIES = {
    'DFSG' : 'License :: DFSG approved',
    'EFS' : 'License :: Eiffel Forum License (EFL)',
    'NPL' : 'License :: Netscape Public License (NPL)',
    'ASL' : 'License :: OSI Approved :: Apache Software License',
    'BSD' : 'License :: OSI Approved :: BSD License',
    'FDL' : 'License :: OSI Approved :: GNU Free Documentation License (FDL)',
    'GPL' : 'License :: OSI Approved :: GNU General Public License (GPL)',
    'LGPL' : 'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
    'MIT' : 'License :: OSI Approved :: MIT License',
    'MPL' : 'License :: OSI Approved :: Mozilla Public License 1.0 (MPL)',
    'MPL11' : 'License :: OSI Approved :: Mozilla Public License 1.1 (MPL 1.1)',
    'QPL' : 'License :: OSI Approved :: Qt Public License (QPL)',
    'ZPL' : 'License :: OSI Approved :: Zope Public License',
    }


def wrap_help_paras(wrapper, text):
    """Given a string containing embedded paras, output wrapped"""

    for idx, para in enumerate(text.split("\n\n")):
        if idx:
            print
        print wrapper.fill(para)

def get_zopeskel_prefs():
    # http://snipplr.com/view/7354/get-home-directory-path--in-python-win-lin-other/
    try:
        from win32com.shell import shellcon, shell
        homedir = shell.SHGetFolderPath(0, shellcon.CSIDL_APPDATA, 0, 0)
    except ImportError: # quick semi-nasty fallback for non-windows/win32com case
        homedir = os.path.expanduser("~")

    # Get defaults from .zopeskel
    config = SafeConfigParser()
    config.read('%s/.zopeskel' % homedir)
    return config

def get_var(vars, name):
    for var in vars:
        if var.name == name:
            return var
    else:
        raise ValueError("No such var: %r" % name)


def update_setup_cfg(path, section, option, value):

    parser = ConfigParser.ConfigParser()
    if os.path.exists(path):
        parser.read(path)

    if not parser.has_section(section):
        parser.add_section(section)

    parser.set(section, option, value)
    parser.write(open(path, 'w'))


class BaseTemplate(templates.Template):
    """Base template for all ZopeSkel templates"""

    #a zopeskel template has to set this to True if it wants to use
    #localcommand
    use_local_commands = False
    null_value_marker = []
    pre_run_msg = None
    post_run_msg = None

    vars = [
        StringChoiceVar(
            'expert_mode',
            title='Expert Mode?',
            description='What question mode would you like? (easy/expert/all)?',
            page='Begin',
            default='easy',
            choices=('easy','expert','all'),
            help="""
In easy mode, you will be asked fewer, more common questions.

In expert mode, you will be asked to answer more advanced,
technical questions.

In all mode, no questions will be skipped--even things like
author_email, which would normally be a default set in a
$HOME/.zopeskel file.
"""),
    ]

    #this is just to be able to add ZopeSkel to the list of paster_plugins if
    #the use_local_commands is set to true and to write a zopeskel section in
    #setup.cfg file containing the name of the parent template.
    #it will be used by addcontent command to list the apropriate subtemplates
    #for the generated project. the post method is not a candidate because
    #many templates override it
    def run(self, command, output_dir, vars):

        if self.use_local_commands and 'ZopeSkel' not in self.egg_plugins:
            self.egg_plugins.append('ZopeSkel')

        templates.Template.run(self, command, output_dir, vars)

        setup_cfg = os.path.join(output_dir, 'setup.cfg')
        if self.use_local_commands:
            update_setup_cfg(setup_cfg, 'zopeskel', 'template', self.name)

    def print_subtemplate_notice(self, output_dir=None):
            """Print a notice about local commands being availabe (if this is
            indeed the case).

            Unfortunately for us, at this stage in the process, the
            egg_info directory has not yet been created (and won't be
            within the scope of this template running [see
            paste.script.create_distro.py]), so we cannot show which
            subtemplates are available.
            """
            plugins = pluginlib.resolve_plugins(['ZopeSkel'])
            commands = pluginlib.load_commands_from_plugins(plugins)
            if not commands:
                return
            commands = commands.items()
            commands.sort()
            longest = max([len(n) for n, c in commands])
            print_commands = []
            for name, command in commands:
                name = name + ' ' * (longest - len(name))
                print_commands.append('  %s  %s' % (name,
                                                    command.load().summary))
            print_commands = '\n'.join(print_commands)
            print '-' * 78
            print """\
The project you just created has local commands. These can be used from within
the product.

usage: paster COMMAND

Commands:
%s

For more information: paster help COMMAND""" % print_commands
            print '-' * 78

    def print_zopeskel_message(self, msg_name):
        """ print a message stored as an attribute of the template
        """
        msg = getattr(self, msg_name, None)
        if msg:
            textwrapper = TextWrapper(
                    initial_indent="**  ",
                    subsequent_indent="**  ",
                    )
            print "\n" + '*'*74
            wrap_help_paras(textwrapper, msg)
            print '*'*74 + "\n"

    def pre(self, *args, **kwargs):
        templates.Template.pre(self, *args, **kwargs)

    def get_template_stack(self, command):
        """ return a list of the template objects being run through in the given command
        """
        asked_tmpls = command.options.templates or ['basic_package']
        templates = []
        for tmpl_name in asked_tmpls:
            command.extend_templates(templates, tmpl_name)
        return [tmpl_obj for tmpl_name, tmpl_obj in templates]

    def get_position_in_stack(self, stack):
        """ return the index of the currently running template in the overall stack
        """
        class_stack = [t.__class__ for t in stack]

        return class_stack.index(self.__class__)

    def should_print_subcommands(self, command):
        """ return true or false

            if this template has subcommands _and_ is the last template
            to be run through that does, go ahead and return true, otherwise
            return false
        """
        if not getattr(self, 'use_local_commands', False):
            return False
        # we have local commands for this template, is it the last one for
        # which this is true?
        stack = self.get_template_stack(command)
        index = self.get_position_in_stack(stack)
        remaining_stack = stack[index+1:]
        have_subcommands_left = [getattr(t, 'use_local_commands', False)
                                 for t in remaining_stack]
        if True in have_subcommands_left:
            return False

        return True

    def post(self, command, output_dir, vars):
        if self.should_print_subcommands(command):
            self.print_subtemplate_notice()
        templates.Template.post(self, command, output_dir, vars)
        # at the very end of it all, print the post_run_msg so we can
        # inform users of important information.
        self.print_zopeskel_message('post_run_msg')

    def _filter_for_modes(self, mode, expected_vars):
        """Filter questions down according to our mode.

        ALL = show all questions
        EASY, EXPERT = show just those
        """

        if mode == ALL: return {}

        hidden = {}

        for var in expected_vars:
            # if in expert mode, hide vars not for expert mode
            if  mode not in var.modes:
                hidden[var.name] = var.default

        return hidden

    def override_package_names_defaults(self, vars, expect_vars):
        """Override package names defaults using project title.

        Override the default for namespace_package, namespace_package2,
        and package from splitting the project title--if ndots is
        specified by this template.

        This is helpful for new users, who find it confusing to provide
        a package name like "mycompany.theme.blue" and then have to
        (slightly-redundantly) specify namespace_package=mycompany,
        namespace_package2=theme, package=blue.
        """

        ndots = getattr(self, 'ndots', None)
        if ndots:
            parts = vars['project'].split(".")
            if ndots >= 1 and len(parts) >= 1:
                get_var(expect_vars, 'namespace_package').default = parts[0]
            if ndots >= 2 and len(parts) >= 2:
                get_var(expect_vars, 'namespace_package2').default = parts[1]
            package_name = parts[-1]
            get_var(expect_vars, 'package').default = package_name

    def check_vars(self, vars, cmd):
        # if we need to notify users of anything before they start this
        # whole process, we can do it here.
        self.print_zopeskel_message('pre_run_msg')

        # Copied and modified from PasteScript's check_vars--
        # the method there wasn't hookable for the things
        # we need -- question posing, validation, etc.
        #
        # Admittedly, this could be merged into PasteScript,
        # but it was decided it was easier to limit scope of
        # these changes to ZopeSkel, as other projects may
        # use PasteScript in very different ways.


        cmd._deleted_once = 1      # don't re-del package

        textwrapper = TextWrapper(
                initial_indent="|  ",
                subsequent_indent="|  ",
                )

        # now, mostly copied direct from paster
        expect_vars = self.read_vars(cmd)
        if not expect_vars:
            # Assume that variables aren't defined
            return vars
        converted_vars = {}
        errors = []

        config = get_zopeskel_prefs()
        # pastescript allows one to request more than one template (multiple
        # -t options at the command line) so we will get a list of templates
        # from the cmd's options property
        requested_templates = cmd.options.templates
        for var in expect_vars:
            for template in requested_templates:
                if config.has_option(template, var.name):
                    var.default = config.get(template, var.name)
                    break
            else:
                # Not found in template section, now look explicitly
                # in DEFAULT section
                if config.has_option('DEFAULT', var.name):
                    var.default = config.get('DEFAULT', var.name)

        self.override_package_names_defaults(vars, expect_vars)

        unused_vars = vars.copy()

        for var in expect_vars:
            if var.name not in unused_vars:
                if cmd.interactive:
                    prompt = var.pretty_description()
                    response = self.null_value_marker
                    while response is self.null_value_marker:
                        response = cmd.challenge(prompt, var.default, var.should_echo)
                        if response == '?':
                            help = var.further_help().strip() % converted_vars
                            print
                            wrap_help_paras(textwrapper, help)
                            print
                            response = self.null_value_marker;
                        if response is not self.null_value_marker:
                            try:
                                response = var.validate(response)
                            except ValidationException, e:
                                print e
                                response = self.null_value_marker;
                    converted_vars[var.name] = response
                elif var.default is command.NoDefault:
                    errors.append('Required variable missing: %s'
                                  % var.full_description())
                else:
                    converted_vars[var.name] = var.default
            else:
                converted_vars[var.name] = unused_vars.pop(var.name)

            # filter the vars for mode.
            if var.name == 'expert_mode':
                expert_mode = converted_vars['expert_mode']
                hidden = self._filter_for_modes(expert_mode, expect_vars)
                unused_vars.update(hidden)

        if errors:
            raise command.BadCommand(
                'Errors in variables:\n%s' % '\n'.join(errors))
        converted_vars.update(unused_vars)
        vars.update(converted_vars)

        result = converted_vars

        return result

    @property
    def pages(self):
        pages = []
        page_map = {}
        for question in self.vars:
            name = question.page
            if name in page_map:
                page = page_map[name]
                page['vars'].append(question)
            else:
                page = {'name': name, 'vars': [question]}
                pages.append(page)
                page_map[name] = page
        return pages
