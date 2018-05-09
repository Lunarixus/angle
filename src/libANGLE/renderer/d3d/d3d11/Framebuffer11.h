//
// Copyright 2014 The ANGLE Project Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
//

// Framebuffer11.h: Defines the Framebuffer11 class.

#ifndef LIBANGLE_RENDERER_D3D_D3D11_FRAMBUFFER11_H_
#define LIBANGLE_RENDERER_D3D_D3D11_FRAMBUFFER11_H_

#include "libANGLE/Observer.h"
#include "libANGLE/renderer/RenderTargetCache.h"
#include "libANGLE/renderer/d3d/FramebufferD3D.h"
#include "libANGLE/renderer/d3d/d3d11/renderer11_utils.h"

namespace rx
{
class Renderer11;

class Framebuffer11 : public FramebufferD3D
{
  public:
    Framebuffer11(const gl::FramebufferState &data, Renderer11 *renderer);
    ~Framebuffer11() override;

    gl::Error discard(const gl::Context *context, size_t count, const GLenum *attachments) override;
    gl::Error invalidate(const gl::Context *context,
                         size_t count,
                         const GLenum *attachments) override;
    gl::Error invalidateSub(const gl::Context *context,
                            size_t count,
                            const GLenum *attachments,
                            const gl::Rectangle &area) override;

    // Invalidate the cached swizzles of all bound texture attachments.
    gl::Error markAttachmentsDirty(const gl::Context *context) const;

    gl::Error syncState(const gl::Context *context,
                        const gl::Framebuffer::DirtyBits &dirtyBits) override;

    const gl::AttachmentArray<RenderTarget11 *> &getCachedColorRenderTargets() const
    {
        return mRenderTargetCache.getColors();
    }
    const RenderTarget11 *getCachedDepthStencilRenderTarget() const
    {
        return mRenderTargetCache.getDepthStencil();
    }

    RenderTarget11 *getFirstRenderTarget() const;

    gl::Error getSamplePosition(const gl::Context *context,
                                size_t index,
                                GLfloat *xy) const override;

  private:
    gl::Error clearImpl(const gl::Context *context, const ClearParameters &clearParams) override;

    gl::Error readPixelsImpl(const gl::Context *context,
                             const gl::Rectangle &area,
                             GLenum format,
                             GLenum type,
                             size_t outputPitch,
                             const gl::PixelPackState &pack,
                             uint8_t *pixels) override;

    gl::Error blitImpl(const gl::Context *context,
                       const gl::Rectangle &sourceArea,
                       const gl::Rectangle &destArea,
                       const gl::Rectangle *scissor,
                       bool blitRenderTarget,
                       bool blitDepth,
                       bool blitStencil,
                       GLenum filter,
                       const gl::Framebuffer *sourceFramebuffer) override;

    gl::Error invalidateBase(const gl::Context *context,
                             size_t count,
                             const GLenum *attachments,
                             bool useEXTBehavior) const;
    gl::Error invalidateAttachment(const gl::Context *context,
                                   const gl::FramebufferAttachment *attachment) const;

    GLenum getRenderTargetImplementationFormat(RenderTargetD3D *renderTarget) const override;

    Renderer11 *const mRenderer;
    RenderTargetCache<RenderTarget11> mRenderTargetCache;
};

}  // namespace rx

#endif // LIBANGLE_RENDERER_D3D_D3D11_FRAMBUFFER11_H_
