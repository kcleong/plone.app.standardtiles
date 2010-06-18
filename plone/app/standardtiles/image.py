from zope.interface import directlyProvides, implements
from zope import schema
from zope.schema.vocabulary import SimpleVocabulary
from zope.schema.interfaces import IVocabularyFactory
from zope.publisher.interfaces import NotFound
from zope.publisher.interfaces import IPublishTraverse
from zope.app.component.hooks import getSite

from plone.directives import form as directivesform

from plone.tiles import Tile

from plone.namedfile.utils import set_headers, stream_data

from Products.CMFCore.utils import getToolByName
from Products.ATContentTypes.interfaces import IATImage


def availableImagesVocabulary(context):
    """Vocabulary composed of ATImages inside the '/images' folder
    of the site root.
    """
    site = getSite()  # the real context is lost somewhat
    catalog = getToolByName(site, 'portal_catalog')
    portal_state = site.restrictedTraverse('@@plone_portal_state')
    root_path = portal_state.navigation_root_path()
    images_path = root_path + '/images'
    results = catalog(path=images_path,
                      object_provides=IATImage.__identifier__)
    items = [(r.id, r.id) for r in results]
    return SimpleVocabulary.fromItems(items)
directlyProvides(availableImagesVocabulary, IVocabularyFactory)


class IImageTile(directivesform.Schema):

    imageUID = schema.Choice(title=u"Image UID", required=True,
                             vocabulary="Available Images")
    altText = schema.TextLine(title=u"Alternative text", required=False)


class ImageTile(Tile):
    """Image tile.
    
    This is a persistent tile which stores an image and optionally alt
    text. When rendered, the tile will output an <img /> tag like::
    
        <img src="http://.../@@plone.app.standardtiles.image/tile-id/@@download/filename.gif" />
    
    The tile is a publish traversal view, so it will stream the file data
    if the correct filename (matching the uploaded filename), is given in
    the traversal subpath (filename.gif in the example above). Note that the
    ``id`` query string parameter is still required for the tile to be able to
    access its persistent data.
    """

    def __call__(self):
        # Not for production use - this should be in a template!
        imageUID = self.data.get('imageUID')
        image = getattr(self.context.images, imageUID, None)
        if image is not None:
            altText = self.data.get('altText')
            if altText is not None:
                altText = altText.replace('"', '\"')
            else:
                altText = image.Title()
            imageURL = image.absolute_url() + '/image'
            return '<html><body><img src="%s" alt="%s" /></body></html>' % (imageURL, altText)
        else:
            return '<html><body><em>Image not found.</em></body></html>'

class ImageTileDownload(object):
    """Implementation of the @@download view on the image tile.
    
    This is a view onto the ImageTile tile view.
    """
    
    implements(IPublishTraverse)
    filename = None
    
    def publishTraverse(self, request, name):
        if self.filename is None:
            self.filename = name
            return self
        raise NotFound(name)
    
    def __call__(self):
        """Render the file to the browser
        """
        
        image = self.context.data.get('image', None)
        if image is None:
            raise NotFound(self, self.filename, self.request)
        
        if not self.filename:
            self.filename = getattr(image, 'filename', '')
        
        set_headers(image, self.request.response, filename=self.filename)
        return stream_data(image)
