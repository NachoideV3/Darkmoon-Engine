#ifndef MESH_HLSL
#define MESH_HLSL

#include "pack_unpack.hlsl"

struct VertexPacked {
	float4 data0;
};

struct Mesh {
    uint vertex_core_offset;
    uint vertex_uv_offset;
    uint vertex_mat_offset;
    uint vertex_aux_offset;
    uint vertex_tangent_offset;
    uint mat_data_offset;
    uint index_offset;
};

struct Vertex {
    float3 position;
    float3 normal;
};

// TODO: nuke
float3 unpack_unit_direction_11_10_11(uint pck) {
    return float3(
        float(pck & ((1u << 11u)-1u)) * (2.0f / float((1u << 11u)-1u)) - 1.0f,
        float((pck >> 11u) & ((1u << 10u)-1u)) * (2.0f / float((1u << 10u)-1u)) - 1.0f,
        float((pck >> 21u)) * (2.0f / float((1u << 11u)-1u)) - 1.0f
    );
}

Vertex unpack_vertex(VertexPacked p) {
    Vertex res;
    res.position = p.data0.xyz;
    res.normal = unpack_unit_direction_11_10_11(asuint(p.data0.w));
    return res;
}

VertexPacked pack_vertex(Vertex v) {
    VertexPacked p;
    p.data0.xyz = v.position;
    p.data0.w = pack_normal_11_10_11(v.normal);
    return p;
}

static const uint MESH_MATERIAL_FLAG_EMISSIVE_USED_AS_LIGHT = 1;

// Map indices for the maps array
static const uint MAP_INDEX_NORMAL = 0;
static const uint MAP_INDEX_SPEC = 1;
static const uint MAP_INDEX_ALBEDO = 2;
static const uint MAP_INDEX_EMISSIVE = 3;

struct MeshMaterial {
    float base_color_mult[4];
    uint maps[4];  // Changed to match Rust structure
    float roughness_mult;
    float metalness_factor;
    float emissive[3];
    uint flags;
    float map_transforms[6 * 4];
    float transparency;    // 0.0 = opaque, 1.0 = fully transparent
    float ior;            // Index of refraction for translucent materials
    float transmission;   // Transmission factor (0.0-1.0)
    float _padding;       // For alignment
};

float2 transform_material_uv(MeshMaterial mat, float2 uv, uint map_idx) {
    uint xo = map_idx * 6;
    float2x2 rot_scl = float2x2(mat.map_transforms[xo+0], mat.map_transforms[xo+1], mat.map_transforms[xo+2], mat.map_transforms[xo+3]);
    float2 offset = float2(mat.map_transforms[xo+4], mat.map_transforms[xo+5]);
    return mul(rot_scl, uv) + offset;
}

bool is_material_translucent(MeshMaterial mat) {
    return mat.transparency > 0.01 || mat.transmission > 0.01;
}

float get_material_alpha(MeshMaterial mat) {
    return 1.0 - mat.transparency;
}


#endif