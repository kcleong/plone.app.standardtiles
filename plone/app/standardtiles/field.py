from z3c.form.form import DisplayForm
from z3c.form.field import Fields
from plone.dexterity.utils import iterSchemata
from plone.tiles import Tile
from plone.autoform.interfaces import WIDGETS_KEY
from plone.autoform.utils import resolveDottedName
from plone.z3cform import z2


class DexterityFieldTile(Tile):
    """Field tile for Dexterity content
    """

    def __init__(self, context, request):
        super(DexterityFieldTile, self).__init__(context, request)
        self.form = DisplayForm(context, request)
        self.fieldname = self.data['field']
        
        for schema in iterSchemata(self.context):
            if self.fieldname in schema:
                # XXX: will this work if there's more than one fields
                # with the same name in different schemas? One should
                # be able to use interface.fieldname instead.
                self.schema = schema
                self.form.fields = Fields(schema[self.fieldname])
                return

        raise KeyError('Field with name %s not found.' % self.fieldname)

    def update(self):
        factory = self.schema.getTaggedValue(WIDGETS_KEY)[self.fieldname]
        if self.form.fields[self.fieldname].widgetFactory.get(self.form.mode, None) is None:
            if isinstance(factory, basestring):
                factory = resolveDottedName(factory)
            self.form.fields[self.fieldname].widgetFactory = factory
        self.form.update()

    def _wrap_widget(self, render):
        return u"<html><body>%s</body></html>" % render

    def __call__(self):
        z2.switch_on(self)
        self.update()
        return self._wrap_widget(self.form.widgets[self.fieldname].render())
